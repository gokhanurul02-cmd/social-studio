"""Perceptual measurements; optional networks must have local pretrained weights."""
import importlib.util
import os
from pathlib import Path


def ssim(a, b):
    import cv2
    import numpy as np
    x, y = a.astype('float64'), b.astype('float64')
    mx, my = cv2.GaussianBlur(x, (11, 11), 1.5), cv2.GaussianBlur(y, (11, 11), 1.5)
    vx = cv2.GaussianBlur(x * x, (11, 11), 1.5) - mx * mx
    vy = cv2.GaussianBlur(y * y, (11, 11), 1.5) - my * my
    cov = cv2.GaussianBlur(x * y, (11, 11), 1.5) - mx * my
    score = ((2 * mx * my + 6.5025) * (2 * cov + 58.5225)) / ((mx * mx + my * my + 6.5025) * (vx + vy + 58.5225))
    return float(np.mean(score[5:-5, 5:-5] if min(score.shape[:2]) > 10 else score))


class OptionalMetrics:
    def __init__(self):
        self.lpips_model = None
        self.clip_model = None
        self.status = {}
        if importlib.util.find_spec('torch') is None:
            self.status = {name: {'skipped': 'torch unavailable'} for name in ['lpips', 'clip']}
            return
        try:
            import torch
        except Exception as exc:
            self.status = {name: {'skipped': f'torch failed to load: {exc}'} for name in ['lpips', 'clip']}
            return
        self.torch = torch
        if importlib.util.find_spec('lpips') is not None:
            backbone = Path(torch.hub.get_dir()) / 'checkpoints/alexnet-owt-7be5be79.pth'
            if backbone.is_file():
                try:
                    import lpips
                    from unittest.mock import patch
                    # Never let torchvision fetch weights as a side effect of a comparison.
                    with patch('torch.hub.download_url_to_file', side_effect=RuntimeError('Network downloads disabled')):
                        self.lpips_model = lpips.LPIPS(net='alex', verbose=False).eval()
                    self.status['lpips'] = {'method': 'LPIPS AlexNet, locally cached pretrained weights', 'confidence': 'model distance'}
                except Exception as exc:
                    self.status['lpips'] = {'skipped': str(exc)}
            else:
                self.status['lpips'] = {'skipped': 'Pretrained AlexNet backbone not cached; download explicitly before use'}
        else:
            self.status['lpips'] = {'skipped': 'lpips unavailable'}
        weights = os.environ.get('SOCIAL_CLIP_WEIGHTS')
        if importlib.util.find_spec('open_clip') is not None and weights and Path(weights).is_file():
            try:
                import open_clip
                self.clip_model, _, self.preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained=weights)
                self.clip_model.eval()
                self.status['clip'] = {'method': 'ViT-B-32 image embedding cosine, local SOCIAL_CLIP_WEIGHTS', 'confidence': 'model similarity'}
            except Exception as exc:
                self.status['clip'] = {'skipped': str(exc)}
        else:
            self.status['clip'] = {'skipped': 'open_clip or local SOCIAL_CLIP_WEIGHTS unavailable'}

    def score(self, a, b):
        try:
            return self._score(a, b)
        except Exception as exc:
            for name in ['lpips', 'clip']:
                if 'skipped' not in self.status.get(name, {}):
                    self.status[name] = {'skipped': f'Optional model inference failed: {exc}'}
            self.lpips_model = self.clip_model = None
            return {}

    def _score(self, a, b):
        from PIL import Image
        result = {}
        if self.lpips_model is None and self.clip_model is None:
            return result
        torch = self.torch
        with torch.inference_mode():
            if self.lpips_model is not None:
                tensors = [torch.from_numpy(image[:, :, ::-1].copy()).permute(2, 0, 1).float().unsqueeze(0) / 127.5 - 1 for image in [a, b]]
                result['lpips'] = float(self.lpips_model(*tensors).item())
            if self.clip_model is not None:
                tensors = torch.stack([self.preprocess(Image.fromarray(image[:, :, ::-1].astype('uint8'))) for image in [a, b]])
                embeddings = self.clip_model.encode_image(tensors)
                embeddings /= embeddings.norm(dim=-1, keepdim=True)
                result['clip_cosine'] = float((embeddings[0] * embeddings[1]).sum().item())
        return result


def audio_delay(source, rendered, sample_rate=16000):
    import numpy as np
    if not len(source) or not len(rendered):
        return {'skipped': 'Empty audio cannot define a delay'}
    a, b = source.astype(float), rendered.astype(float)
    a, b = a - a.mean(), b - b.mean()
    norm = float(np.linalg.norm(a) * np.linalg.norm(b))
    if norm < 1e-10:
        return {'skipped': 'Silent or constant audio does not define a delay'}
    size = 1 << (len(a) + len(b) - 1).bit_length()
    correlation = np.fft.irfft(np.fft.rfft(b, size) * np.conj(np.fft.rfft(a, size)), size)
    limit = min(sample_rate * 10, len(a) - 1, len(b) - 1)
    lags = np.arange(-limit, limit + 1)
    values = correlation[lags % size] / norm
    index = int(np.argmax(values))
    return {'delay_ms': float(lags[index] * 1000 / sample_rate), 'confidence': float(values[index]),
            'confidence_kind': 'normalized correlation peak, not probability',
            'method': 'FFT cross correlation of demeaned mono PCM; positive means render is late',
            'search_window_s': limit / sample_rate, 'note': 'Periodic audio may produce ambiguous peaks'}


def match_times(a, b, fps, tolerance=.5):
    available = set(range(len(b)))
    matches = []
    for start in a:
        if not available:
            break
        index = min(available, key=lambda i: abs(b[i] - start))
        delta = b[index] - start
        if abs(delta) <= tolerance:
            available.remove(index)
            matches.append({'source': start, 'render': b[index], 'delta_frames': delta * fps})
    return {'matches': matches, 'unmatched_source': len(a) - len(matches), 'unmatched_render': len(b) - len(matches),
            'mean_absolute_delta_frames': sum(abs(r['delta_frames']) for r in matches) / len(matches) if matches else None,
            'match_ratio': 2 * len(matches) / (len(a) + len(b)) if a or b else None,
            'tolerance_s': tolerance, 'method': 'one-to-one nearest temporal events', 'confidence': 'detector dependent'}

"""Backward-compatible CLI and Python import entry point."""
import sys
from social_studio import cli

if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    try:
        cli.main()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:
        print(f'HATA: {exc}', file=sys.stderr)
        sys.exit(1)
else:
    sys.modules[__name__] = cli

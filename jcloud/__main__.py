def main():
    from .parsers import get_main_parser
    import os

    args = get_main_parser().parse_args()

    if args.loglevel:
        os.environ['JCLOUD_LOGLEVEL'] = args.loglevel

    try:
        import threading
        from .helper import is_latest_version

        threading.Thread(
            target=is_latest_version, daemon=True, args=('jcloud',)
        ).start()
        from jcloud import api

        getattr(api, args.cli.replace('-', '_'))(args)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()

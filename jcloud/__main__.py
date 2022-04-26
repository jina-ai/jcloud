def main():
    from .parsers import get_main_parser
    import os

    args = get_main_parser().parse_args()

    if args.loglevel:
        os.environ['JCLOUD_LOGLEVEL'] = args.loglevel

    try:
        from .helper import is_latest_version

        is_latest_version()
        from jcloud import api

        getattr(api, args.cli.replace('-', '_'))(args)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()

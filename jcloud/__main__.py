def main():
    import logging
    import os

    from .parsers import get_main_parser

    args = get_main_parser().parse_args()
    if args.loglevel:
        os.environ['JCLOUD_LOGLEVEL'] = args.loglevel

    logging.getLogger('asyncio').setLevel(logging.WARNING)

    try:
        if 'NO_VERSION_CHECK' not in os.environ:
            from .helper import is_latest_version

            is_latest_version()
        from jcloud import api

        if hasattr(args, 'subcommand'):
            getattr(api, args.subcommand.replace('-', '_'))(args)
        else:
            getattr(api, args.jc_cli.replace('-', '_'))(args)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()

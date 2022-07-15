import webbrowser

from rich import print
from hubble.utils.config import config

from .helper import get_logger

logger = get_logger()


class Survey:
    def count(self) -> 'Survey':
        config.set('success_deploys', self.num_successful_deploys + 1)
        return self

    @property
    def num_successful_deploys(self) -> int:
        return config.get('success_deploys') or 0

    @property
    def is_asked(self) -> bool:
        return config.get('is_survey_done') or False

    def ask(self, threshold: int = 3) -> 'Survey':
        if threshold < 0 or (
            self.num_successful_deploys >= threshold and not self.is_asked
        ):
            from rich.markdown import Markdown
            from rich.prompt import Confirm

            is_survey = Confirm.ask(
                '[cyan]:bow: Would you like to take a quick survey about your user experience?\n'
                'It will only take [b]5 minutes[/b] but can help us understanding your usage better.[/cyan]\n'
                '[dim]a Google Form will be opened in your browser when typing [b]y[/b][/dim]'
            )
            if is_survey:
                webbrowser.open('https://forms.gle/1yEwNfh7pzeibxQy6', new=2)
                print(
                    Markdown(
                        '''
- If your browser does nothing, please [open this URL](https://forms.gle/1yEwNfh7pzeibxQy6).
- If your want to modify a submitted survey, or fill in later, please do `jc survey` in the terminal.
                '''
                    )
                )
                config.set('is_survey_done', True)
            else:
                print(
                    'No worries. When you have some free time, please consider doing [b]jc survey[/b] in the terminal 🙂'
                )
        return self

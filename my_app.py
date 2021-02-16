import csv
import json
import datetime as dt
import concurrent.futures

import requests
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel


class Main(Screen):
    pass


class MyBox(BoxLayout):
    pass


class Practice(Screen):
    input = ObjectProperty(None)
    output = ObjectProperty(None)
    practice_text = ObjectProperty(None)
    meaning_viewer = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(Practice, self).__init__(**kwargs)
        self.text = []
        self.text_len = 0
        self._keyboard = Window.request_keyboard(
            self._keyboard_closed, self, 'text')
        self.erase_text = False
        self.show_text = True
        self.memorize_text = False
        self.text_copy = self.practice_text.text
        self.idx = 0

    def on_enter(self, *args):
        if self.text:
            self.keyboard_on()

    def copy_mode(self):
        self.memorize_text = False
        Snackbar(text="you are in copy mode").show()

    def memorize_mode(self):
        self.memorize_text = True
        Snackbar(text="you are in memorize mode").show()

    def keyboard_on(self):
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if self.erase_text:  # false by default
            self.output.text = ''
            self.erase_text = False
        try:
            self.output.text += text
        except TypeError:

            if keycode[1] == 'backspace':
                self.output.text = self.output.text[:-1]
            if keycode[1] == 'enter':
                if self.memorize_text:
                    self.practice_text.text = self.text_copy
                if self.output.text != self.practice_text.text:
                    self.show_wrong()
                    self.erase_text = True
                else:
                    self.show_right()
                    self.set_practice_text()
                    self.erase_text = True
        if keycode[1] == 'escape':
            keyboard.release()
        return True

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)

    def parse(self):
        lower = self.input.text.lower()
        self.text = ''.join(list(map(self.return_char, lower))).split()

    @staticmethod
    def return_char(x):
        return x if x in 'abcdefghijklmnopqurstvwxyz ' else ' '

    def set_practice_text(self, *args):
        if self.show_text:
            self.text = self.text[self.idx:]
            self.text_len += 4
            self.practice_text.text = ' '.join(self.text[:self.get_matching_words_len(
                self.text_len, self.text)])
            if self.memorize_text:
                self.show_text = False
                self.practice_text.text_copy = self.practice_text.text[:]
                Clock.schedule_once(self.set_practice_text, 5)
                self._keyboard_closed()
        else:
            self.practice_text.text = ''
            self.keyboard_on()
            self.show_text = True

    def get_matching_words_len(self, char_len, words_list):
        self.idx = 0
        words_len = 0
        for word in words_list:
            self.idx += 1
            words_len += len(word)
            if words_len >= char_len:
                if words_len - char_len > 2:
                    self.idx -= 1
                    return self.idx
                return self.idx

    def show_right(self):
        self.output.text = '[color=009409]' + self.output.text + '[/color]'  # green
        self.output.markup = True

    def show_wrong(self):
        output_list = []
        for output, practice in zip(self.output.text.split(), self.practice_text.text.split()):
            if output != practice:
                output = '[color=FF0004]' + output + '[/color]'  # red
                self._save_got_wrong_word(practice)
            output_list.append(output)
        self.output.text = ' '.join(output_list)
        self.output.markup = True
        self.text_len -= 4

    def _save_got_wrong_word(self, word):
        with open('words_to_revise.csv', 'a') as file:
            w = csv.writer(file)
            w.writerow([word, self.get_revision_date(1), '1'])

    @staticmethod
    def get_revision_date(days):
        delta = dt.timedelta(days=int(days))
        today = dt.date.today()
        return today + delta

    def display_words_meaning(self):
        self.meaning_viewer.clear_widgets()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(self.display_word_meaning, self.output.text.split())

    def display_word_meaning(self, word):
        word_meaning = self.get_meaning(word)
        if word_meaning:
            wid = self.add_word_meaning_to_widget(word_meaning)
            self.meaning_viewer.add_widget(wid)

    def get_meaning(self, word):
        try:
            file = requests.get(f'https://api.dictionaryapi.dev/api/v1/entries/en/{word}')
            file = json.loads(file.text)
            dict_ = file[0]
            dict_ = dict_['word'], dict_['meaning']
            return dict_
        except requests.exceptions.RequestException:
            self.show_alert_dialog("you're offline", "you need to have an internet connection "
                                                     "to see words meaning! check your network and then try again")
        except KeyError:
            pass

    def show_alert_dialog(self, title, text):
        btn = MDFlatButton(text="ok", text_color=app.theme_cls.primary_color,)
        btn.bind(on_press=lambda x: self.remove_widget(dialog))

        dialog = MDDialog(size_hint=(.8, None), title=title, text=text, buttons=[btn])
        dialog.open()

    @staticmethod
    def add_word_meaning_to_widget(word_meaning):
        box = MyBox(orientation='vertical')
        box.add_widget(MDLabel(text=word_meaning[0], halign="center", font_style='H3'))
        for key, val in word_meaning[1].items():
            box.add_widget(MDLabel(text=' '+key, font_style='H6'))
            for i in val:
                for x, y in i.items():
                    box.add_widget(MDLabel(text=f' {x}: {y}'))
        box.add_widget(MDLabel(text=''))
        return box

    def add_widg(self):
        try:
            self.add_widget(self.ids.start_btn)
            self.add_widget(self.ids.input)

            self.output.text = ''
            self.practice_text.text = ''
            self.practice_text.text_len = 0
            self._keyboard_closed()
        except:
            pass

    def return_(self):
        self.manager.transition.direction = 'right'
        self.manager.current = 'main'

    def on_leave(self, *args):
        self._keyboard_closed()


class Revision(Screen):
    output = ObjectProperty(None)
    practice_text = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(Revision, self).__init__(**kwargs)
        self.practice = Practice(output=self.output, practice_text=self.practice_text)

    def on_enter(self, *args):
        self.practice.keyboard_on()
        self.get_revision_words()
        self.practice.set_practice_text()
        if not self.practice.text:
            Snackbar(text="there are no words to revise today").show()

    def get_revision_words(self):
        with open('words_to_revise.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                d = row['date_to_revise'].split('-')
                r = dt.date(int(d[0]), int(d[1]), int(d[2]))
                if r <= dt.date.today():
                    self.practice.text.append(row['word'])

    def on_leave(self, *args):
        self.practice._keyboard_closed()
        self.set_next_revises()

    def set_next_revises(self):
        with open('words_to_revise.csv', 'r') as file:
            reader = csv.DictReader(file)
            lines = list(reader)
            for line in lines:
                if line['delta'] == '30':
                    lines.remove(line)
                    continue
                line = self.get_next_revise(line)

        with open('words_to_revise.csv', 'w') as file:
            w = csv.DictWriter(file, fieldnames=['word', 'date_to_revise', 'delta'])
            w.writeheader()
            for i in lines:
                w.writerow(i)

    def get_next_revise(self, line):
        d = line['date_to_revise'].split('-')
        r = dt.date(int(d[0]), int(d[1]), int(d[2]))
        if line['word'] not in self.practice.text and r <= dt.date.today():
            delta = self.get_new_delta(line['delta'])
            line['delta'] = delta
            line['date_to_revise'] = self.practice.get_revision_date(delta)
        return line

    def get_new_delta(self, delta):
        delta_dict = {'1': '3', '3': '7', '7': '30'}
        new_delta = delta_dict[delta]
        return new_delta

    def return_(self):
        self.manager.transition.direction = 'right'
        self.manager.current = 'main'


class WordTrainer(MDApp):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(Main(name='main'))
        sm.add_widget(Practice(name='practice'))
        sm.add_widget(Revision(name='revision'))
        return sm


if __name__ == '__main__':
    app = WordTrainer()
    app.run()

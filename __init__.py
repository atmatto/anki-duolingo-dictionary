from aqt import gui_hooks, mw, qt
from aqt.editor import Editor
from anki.notes import Note
from anki.models import NoteType
from typing import List
from pathlib import Path
from uuid import uuid4
import json
import os

nam = qt.QNetworkAccessManager()

def icon() -> str:
	assert mw is not None
	if mw.pm.night_mode():
		return str(Path(__file__).parent.resolve()) + "/icon/black.png"
	else:
		return str(Path(__file__).parent.resolve()) + "/icon/white.png"

class Word:
	def tab(self, search_result, native_language):
		# Contents

		layout = qt.QVBoxLayout()
		layout.setAlignment(qt.Qt.AlignTop)

		word = qt.QLabel()
		word.setText(search_result["text"])
		wf = word.font()
		wf.setPointSize(wf.pointSize() + 5)
		word.setFont(wf)
		layout.addWidget(word)

		translations = qt.QLabel()
		for t in search_result["translations"][native_language]:
			translations.setText(translations.text() + t + ", ")
		if len(translations.text()) > 2:
			translations.setText(translations.text()[:-2])
		layout.addWidget(translations)

		examples = qt.QWidget()
		examples_layout = qt.QVBoxLayout()
		examples_layout.setAlignment(qt.Qt.AlignTop)
		examples_layout.setContentsMargins(8,8,8,8)
		loading = qt.QLabel()
		examples_layout.addWidget(loading)
		examples.setLayout(examples_layout)
		layout.addWidget(examples)

		def paste_example(example):
			def func():
				self.addon_widget.ed.doPaste("<div>" + example + "</div>", False)
				# TODO Find a better way?
			return func

		def show_translation_f(label, text):
			def func():
				label.setText(text)
			return func

		def loaded(dictionary_results):
			loading.setVisible(False)
			loading.setText("Loaded")
			used_examples = set()
			for example in dictionary_results:
				if example["text"] not in used_examples:
					used_examples.add(example["text"])
					example_layout = qt.QHBoxLayout()
					example_layout.setContentsMargins(0,0,0,0)
					example_label = qt.QLabel()
					if config["hide_example_translations"]:
						example_label.setText("<div style=\"font-size: 16pt\">" + conv_html(example["example_sentence"]) + "</div>")
					else:
						example_label.setText("<div style=\"font-size: 16pt\">" + conv_html(example["example_sentence"]) + "</div>" + "<div>" + conv_html(example["translation"]) + "</div>")
					example_button = qt.QPushButton()
					qt.qconnect(example_button.clicked, paste_example(config["example_paste_format"].format(tl=example["text"], nl=example["translation_text"])))
					example_button.setText("")
					example_button.setFixedWidth(20)
					example_button.setFixedHeight(20)
					example_widget = qt.QWidget()
					example_widget.setLayout(example_layout)
					example_layout.addWidget(example_button, 0)
					example_layout.addWidget(example_label, 1)
					if config["hide_example_translations"]:
						show_translation = qt.QPushButton()
						show_translation.setText("Show translation")
						qt.qconnect(show_translation.clicked, show_translation_f(example_label, "<div style=\"font-size: 16pt\">" + conv_html(example["example_sentence"]) + "</div>" + "<div>" + conv_html(example["translation"]) + "</div>"))
						example_layout.addWidget(show_translation, 0)
					examples_layout.addWidget(example_widget)
		

		def clicked():
			if loading.text() != "Loaded":
				loading.setText("Loading examples...")
				self.dictionary_request(search_result["lexemeId"], loaded)
				dictionary_results = list()

		# Tab

		w = qt.QWidget()
		w.setLayout(layout)
		
		s = qt.QScrollArea()
		s.setWidgetResizable(True)
		s.setWidget(w)
		return s, clicked

	def current_changed(self, i: int):
		self.shown_funcs[i]()

	def cleanup(self):
		nam.finished.disconnect(self.on_response)

	def on_response(self, r):
		req_id = r.request().attribute(qt.QNetworkRequest.User)
		w = r.request().attribute(qt.QNetworkRequest.UserMax)
		if req_id in self.waiting_for:
			results = list()
			try:
				results = json.loads(str(r.readAll(), "utf-8"))["alternative_forms"]
			except:
				print("Failed parsing response.")
			self.waiting_for.pop(req_id)(results)

		
	def dictionary_request(self, lexemeId, on_load):
		id = "d."+self.id+":"+lexemeId
		self.waiting_for[id] = on_load
		dictionary(lexemeId, id)

	def __init__(self, search_results, native_language, addon_widget):
		self.addon_widget = addon_widget
		self.widget = qt.QTabWidget()

		self.id = str(uuid4())
		self.waiting_for = {}
		nam.finished.connect(self.on_response)

		qt.qconnect(self.widget.destroyed, lambda p: self.cleanup())

		self.shown_funcs = []
		for r in search_results:
			t, func = self.tab(r, native_language)
			self.widget.addTab(t, r["text"])
			self.shown_funcs.append(func)
			if r["exactMatch"]:
				self.widget.setCurrentWidget(t)
				self.shown_funcs[-1]()
		qt.qconnect(self.widget.currentChanged, lambda i : self.current_changed(i))
		if len(self.shown_funcs) > 0:
			self.shown_funcs[0]()

class Widget:
	def setup_ui(self, ed):
		global config

		splitter = qt.QSplitter(qt.Qt.Vertical)

		self.group_box = qt.QGroupBox()
		self.group_box.setTitle("Duolingo dictionary")

		# Header

		tl_label = qt.QLabel()
		tl_label.setText("Target language:")
		self.tl_selector = qt.QComboBox()
		self.tl_selector.setEditable(True)
		self.tl_selector.addItem("")
		self.tl_selector.addItems(config["target_languages"])
		
		nl_label = qt.QLabel()
		nl_label.setText("Native language:")
		self.nl_selector = qt.QComboBox()
		self.nl_selector.setEditable(True)
		self.nl_selector.addItem("")
		self.nl_selector.addItems(config["native_languages"])
		
		refresh = qt.QPushButton()
		refresh.setText("S&earch main field")
		refresh.setAutoDefault(False)
		qt.qconnect(refresh.clicked, lambda : self.update(True))

		header1 = qt.QWidget()
		header1_layout = qt.QHBoxLayout(header1)
		header1_layout.addWidget(tl_label)
		header1_layout.addWidget(self.tl_selector, 1)
		header1_layout.addWidget(nl_label)
		header1_layout.addWidget(self.nl_selector, 1)
		header1_layout.addSpacing(33)
		header1_layout.addWidget(refresh)
		header1.setLayout(header1_layout)

		field_selector_label = qt.QLabel()
		field_selector_label.setText("Main field:")
		self.field_selector = qt.QComboBox()

		ignored_label = qt.QLabel()
		ignored_label.setText("Ignored words:")
		self.ignored = qt.QLineEdit()

		header2 = qt.QWidget()
		header2_layout = qt.QHBoxLayout(header2)
		header2_layout.addWidget(field_selector_label)
		header2_layout.addWidget(self.field_selector)
		header2_layout.addWidget(ignored_label)
		header2_layout.addWidget(self.ignored)
		header2.setLayout(header2_layout)

		custom_search_label = qt.QLabel()
		custom_search_label.setText("Custom search:")
		self.custom_search = qt.QLineEdit()
		search = qt.QPushButton()
		search.setText("Search")
		search.setAutoDefault(True)
		qt.qconnect(search.clicked, lambda: self.update(True, True))

		header3 = qt.QWidget()
		header3_layout = qt.QHBoxLayout(header3)
		header3_layout.addWidget(custom_search_label)
		header3_layout.addWidget(self.custom_search)
		header3_layout.addWidget(search)
		header3.setLayout(header3_layout)

		# Content

		self.content = qt.QTabWidget()
		self.content.setStyleSheet("QTabWidget::pane {padding:10px;}")

		# QGroupBox

		group_box_layout = qt.QVBoxLayout(self.group_box)
		group_box_layout.setSpacing(8)
		header1_layout.setContentsMargins(8,8,8,0)
		header2_layout.setContentsMargins(8,0,8,0)
		header3_layout.setContentsMargins(8,0,8,0)
		group_box_layout.addWidget(header1)
		group_box_layout.addWidget(header2)
		group_box_layout.addWidget(header3)
		group_box_layout.addWidget(self.content)
		self.group_box.setLayout(group_box_layout)

		# Insert UI to the editor

		ed.widget.layout().addWidget(splitter, 2)
		splitter.addWidget(ed.widget.layout().itemAt(0).widget())
		splitter.addWidget(self.group_box)
		self.group_box.setVisible(False)

		qt.qconnect(self.group_box.destroyed, lambda p: self.cleanup())

		nam.finished.connect(self.on_response)

		self.focus_hook_lambda = lambda n, i: self.update(note=n)
		self.notetype_hook_lambda = lambda nt: self.update()
		gui_hooks.editor_did_focus_field.append(self.focus_hook_lambda)
		gui_hooks.current_note_type_did_change.append(self.notetype_hook_lambda)

	def __init__(self, ed: Editor):
		print(self)
		self.note: Note
		self.ed = ed
		self.is_custom_search = False

		self.id = str(uuid4())
		self.waiting_for = set()

		self.setup_ui(ed)
	
	def cleanup(self):
		gui_hooks.editor_did_focus_field.remove(self.focus_hook_lambda)
		gui_hooks.current_note_type_did_change.remove(self.notetype_hook_lambda)
		nam.finished.disconnect(self.on_response)

	def toggle_ui(self):
		self.group_box.setVisible(not self.group_box.isVisible())

	def search_request(self, languageId, query, uiLanguageId):
		id = "s."+self.id+":"+languageId+"."+uiLanguageId+"."+query
		self.waiting_for.add(id)
		search(languageId, query, uiLanguageId, id)

	def on_response(self, r):
		req_id = r.request().attribute(qt.QNetworkRequest.User)
		w = r.request().attribute(qt.QNetworkRequest.UserMax)
		if req_id in self.waiting_for:
			self.waiting_for.remove(req_id)
			results = list()
			try:
				results = json.loads(str(r.readAll(), "utf-8"))["results"]
			except:
				print("Failed parsing response.")
			self.content.addTab(Word(results, self.nl_selector.currentText(), self).widget, w)

	def update(self, request=False, custom=False, note=None):
		global config

		if not note == None:
			self.note = note

		if not hasattr(self, "note"):
			return

		i = self.field_selector.currentIndex()
		self.field_selector.clear()
		for f in self.note.keys():
			self.field_selector.insertItem(1000, f)
		self.field_selector.setCurrentIndex(i) # 0 if i == -1 else i

		deck = mw.col.decks.name(self.note.note_type()["did"]) # temp, returns default deck for current note type TODO

		if self.nl_selector.currentText() == "":
			self.nl_selector.setCurrentText(parse_deck_rule(config["native_lang"], deck))

		if self.tl_selector.currentText() == "":
			self.tl_selector.setCurrentText(parse_deck_rule(config["target_lang"], deck))

		if self.ignored.text() == "":
			self.ignored.setText(parse_deck_rule(config["ignored_words"], deck))

		if i == -1:
			self.field_selector.setCurrentText(parse_deck_rule(config["main_field"], deck))

		if i == -1:
			self.field_selector.setCurrentIndex(0)

		if request:
			t = ""
			if custom:
				t = self.custom_search.text()
			else:
				for f, c in self.note.items():
					if f == self.field_selector.currentText():
						t = c
						break
			self.content.clear()
			for w in get_words(ignore(t, self.ignored.text())):
				self.search_request(self.tl_selector.currentText(), w, self.nl_selector.currentText())


def parse_deck_rule(s: str, deck: str = "*") -> str:
	# examples:
	# ("English:en;Dutch:nl-NL;*:fr", "English") -> en
	# ("English:en;Dutch:nl-NL;*:fr", "Some other deck") -> fr
	decks = s.split(";")
	try:
		for d in decks:
			dd = d.split(":")[0]
			output = d.split(":")[1]
			if dd == "*" or dd == deck:
				return output
	except:
		print("Couldn't parse deck rule: ", s, deck)
	return ""

def dictionary(lexemeId, req_id):
	url = "https://www.duolingo.com/api/1/dictionary_page?lexeme_id=%s" % lexemeId
	req = qt.QNetworkRequest(qt.QUrl(url))
	req.setAttribute(qt.QNetworkRequest.User, req_id)
	nam.get(req)

def search(languageId, query, uiLanguageId, req_id):
	url = "https://duolingo-lexicon-prod.duolingo.com/api/1/search?exactness=1&languageId=%s&query=%s&uiLanguageId=%s" % (languageId, query, uiLanguageId)
	req = qt.QNetworkRequest(qt.QUrl(url))
	req.setAttribute(qt.QNetworkRequest.User, req_id)
	req.setAttribute(qt.QNetworkRequest.UserMax, query)
	nam.get(req)

def conv_html(s: str) -> str:
	return s.replace("<span class=\"highlighted\">", "<b>").replace("</span>", "</b>")

def ignore(s: str, ignored: str) -> str:
	ignored_list = ignored.split(",")
	ingored_list = list(map(lambda x : x.strip(), ignored_list))
	new = s
	for ig in ignored_list:
		new = new.replace(" " + ig + " ", " ")
		if new.startswith(ig + " "):
			new = new[len(ig)+1:]
		if new.endswith(" " + ig):
			new = new[:-len(ig)-1]
	return new

def get_words(s: str) -> List[str]:
	parens_level = 0
	new = ""
	for c in s:
		if c == "(":
			parens_level += 1
		elif c == ")":
			parens_level -= 1
		elif parens_level == 0:
			new += c
	return list(filter(None, new.split(" ")))

def setup_button(buttons: List[str], ed: Editor) -> None:
	widget = Widget(ed)
	btn = ed.addButton(icon(), str(id(widget)), lambda ed, widget=widget: widget.toggle_ui(), "Duolingo dictionary", toggleable=True, disables=False)
	buttons.insert(-1, btn)

def setup() -> None:
	global config
	config = mw.addonManager.getConfig(__name__)

	gui_hooks.editor_did_init_buttons.append(setup_button)

setup()

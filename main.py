
from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton

from kivy.lang.builder import Builder
from kivy.core.text import LabelBase
from kivy.properties import ObjectProperty , StringProperty
from kivymd.uix.behaviors import  RectangularRippleBehavior  , BackgroundColorBehavior

# ====== MainWidget Header
class HeaderMenu(MDIconButton , RectangularRippleBehavior, BackgroundColorBehavior ) :
	pass

class HeaderBar(BoxLayout) :
	current_screen : str = StringProperty("Envelopes")
	menu : HeaderMenu = ObjectProperty(None)
	header_name : MDLabel = ObjectProperty(None)
	
	def openDrawer(self):
		self.parent.drawer.set_state("open")

# ====== Main Widget 
class MainWidget(BoxLayout) :
	
	dev_logo = "files/transparent.png"

# ====== Main App
class OCEnvelope(MDApp) :
	
	def build(self) :
		return Builder.load_file("design.kv")


if __name__ == "__main__" :
	LabelBase.register(name="font" , fn_regular="fonts/Playground.otf")
	OCEnvelope().run()

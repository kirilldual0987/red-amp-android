"""
Red-Amp Player for Android v1.3
Minimalist Music Player
Author: kirilldual0987
License: MIT
"""

import os
import json
import random
from pathlib import Path

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.uix.progressbar import ProgressBar
from kivy.uix.filechooser import FileChooserListView
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.properties import StringProperty
from kivy.utils import platform

if platform == 'android':
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path, app_storage_path
    request_permissions([
        Permission.READ_EXTERNAL_STORAGE,
        Permission.WRITE_EXTERNAL_STORAGE
    ])

# Colors - Dark theme
C = {
    'bg': (0.1, 0.1, 0.1, 1),
    'bg_dark': (0.05, 0.05, 0.05, 1),
    'bg_light': (0.16, 0.16, 0.16, 1),
    'primary': (0.75, 0.22, 0.17, 1),
    'primary_light': (0.9, 0.3, 0.24, 1),
    'text': (0.82, 0.82, 0.82, 1),
    'text_dim': (0.53, 0.53, 0.53, 1),
    'white': (1, 1, 1, 1),
}


class Track:
    """Track metadata"""
    def __init__(self, path):
        self.path = path
        self.filename = os.path.basename(path)
        self.title = os.path.splitext(self.filename)[0]
        self.artist = "Unknown"
        self.duration = 0
        try:
            self.size = os.path.getsize(path)
        except:
            self.size = 0
    
    @property
    def display_name(self):
        return self.title[:35] + "..." if len(self.title) > 35 else self.title
    
    @property
    def duration_str(self):
        m, s = divmod(int(self.duration), 60)
        return f"{m}:{s:02d}"
    
    def to_dict(self):
        return {
            'path': self.path,
            'title': self.title,
            'duration': self.duration
        }
    
    @classmethod
    def from_dict(cls, d):
        t = cls(d['path'])
        t.title = d.get('title', t.title)
        t.duration = d.get('duration', 0)
        return t


class Player:
    """Audio player"""
    FORMATS = ('.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac')
    
    def __init__(self):
        self.sound = None
        self.tracks = []
        self.index = -1
        self.playing = False
        self.paused = False
        self.volume = 0.7
        self.repeat = 'none'
        self.shuffle = False
        self._shuffle_list = []
        self._position = 0
        self._length = 0
        
        self.on_track = None
        self.on_state = None
        self.on_pos = None
        
        Clock.schedule_interval(self._tick, 0.2)
    
    def set_tracks(self, tracks):
        self.tracks = tracks
        self.index = -1
        self._make_shuffle()
    
    def _make_shuffle(self):
        self._shuffle_list = list(range(len(self.tracks)))
        if self.shuffle:
            random.shuffle(self._shuffle_list)
    
    @property
    def current(self):
        if 0 <= self.index < len(self.tracks):
            i = self._shuffle_list[self.index] if self.shuffle else self.index
            return self.tracks[i]
        return None
    
    @property
    def position(self):
        if self.sound and self.playing:
            return self.sound.get_pos() or 0
        return self._position
    
    @property
    def length(self):
        if self.sound:
            return self.sound.length or self._length
        return self._length
    
    def load(self, idx):
        if not 0 <= idx < len(self.tracks):
            return False
        
        if self.sound:
            self.sound.stop()
            self.sound.unload()
            self.sound = None
        
        self.index = idx
        track = self.current
        if not track or not os.path.exists(track.path):
            return False
        
        try:
            self.sound = SoundLoader.load(track.path)
            if self.sound:
                self.sound.volume = self.volume
                self._length = self.sound.length or 0
                track.duration = self._length
                if self.on_track:
                    self.on_track(track)
                return True
        except:
            pass
        return False
    
    def play(self, idx=None):
        if idx is not None:
            if not self.load(idx):
                return
        
        if not self.sound:
            if self.tracks:
                self.load(0)
            else:
                return
        
        if self.sound:
            self.sound.play()
            self.playing = True
            self.paused = False
            if self.on_state:
                self.on_state('play')
    
    def pause(self):
        if self.sound and self.playing:
            self._position = self.sound.get_pos() or 0
            self.sound.stop()
            self.paused = True
            if self.on_state:
                self.on_state('pause')
    
    def toggle(self):
        if self.playing and not self.paused:
            self.pause()
        else:
            if self.paused and self.sound:
                self.sound.play()
                self.sound.seek(self._position)
                self.paused = False
                if self.on_state:
                    self.on_state('play')
            else:
                self.play()
    
    def next(self):
        if not self.tracks:
            return
        nxt = self.index + 1
        if nxt >= len(self.tracks):
            nxt = 0 if self.repeat == 'all' else len(self.tracks) - 1
        self.load(nxt)
        self.play()
    
    def prev(self):
        if not self.tracks:
            return
        if self.position > 3:
            self.seek(0)
            return
        prv = self.index - 1
        if prv < 0:
            prv = len(self.tracks) - 1 if self.repeat == 'all' else 0
        self.load(prv)
        self.play()
    
    def seek(self, pos):
        if self.sound:
            self.sound.seek(max(0, min(pos, self.length)))
    
    def set_volume(self, v):
        self.volume = max(0, min(1, v))
        if self.sound:
            self.sound.volume = self.volume
    
    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        self._make_shuffle()
        return self.shuffle
    
    def cycle_repeat(self):
        modes = ['none', 'all', 'one']
        self.repeat = modes[(modes.index(self.repeat) + 1) % 3]
        return self.repeat
    
    def _tick(self, dt):
        if self.sound and self.playing and not self.paused:
            pos = self.sound.get_pos()
            if self.on_pos:
                self.on_pos(pos or 0)
            
            if self.sound.state == 'stop' and self.length > 0:
                if self.repeat == 'one':
                    self.play()
                elif self.index < len(self.tracks) - 1:
                    self.next()
                elif self.repeat == 'all':
                    self.index = -1
                    self.next()
                else:
                    self.playing = False
                    if self.on_state:
                        self.on_state('stop')
    
    def scan(self, folder, callback=None):
        tracks = []
        try:
            for root, dirs, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith(self.FORMATS):
                        path = os.path.join(root, f)
                        tracks.append(Track(path))
                        if callback:
                            callback(len(tracks))
        except:
            pass
        return tracks
    
    def cleanup(self):
        if self.sound:
            self.sound.stop()
            self.sound.unload()


class Visualizer(BoxLayout):
    """Audio visualizer"""
    def __init__(self, **kw):
        super().__init__(**kw)
        self.size_hint_y = None
        self.height = dp(70)
        self.bars = [0.0] * 28
        self.active = False
        
        with self.canvas.before:
            Color(*C['bg_dark'])
            self.bg = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self._upd, size=self._upd)
        Clock.schedule_interval(self._anim, 1/25)
    
    def _upd(self, *a):
        self.bg.pos = self.pos
        self.bg.size = self.size
    
    def _anim(self, dt):
        if self.active:
            for i in range(len(self.bars)):
                self.bars[i] += (random.uniform(0.15, 1.0) - self.bars[i]) * 0.28
        else:
            for i in range(len(self.bars)):
                self.bars[i] *= 0.88
        self._draw()
    
    def _draw(self):
        self.canvas.after.clear()
        w, h = self.width, self.height
        if w < 10:
            return
        
        n = len(self.bars)
        bw = max(4, (w - n * 2) / n)
        ox = self.x + (w - (bw + 2) * n) / 2
        
        with self.canvas.after:
            for i, v in enumerate(self.bars):
                bh = v * (h - 8)
                if bh > 1:
                    r = min(1, 0.7 + v * 0.3)
                    g = max(0, 0.35 - v * 0.25)
                    Color(r, g, 0, 1)
                    Rectangle(pos=(ox + i * (bw + 2), self.y + 4), size=(bw, bh))
    
    def set_active(self, a):
        self.active = a


class TrackRow(BoxLayout):
    """Track list item"""
    def __init__(self, track, idx, on_tap, **kw):
        super().__init__(
            orientation='vertical',
            size_hint_y=None,
            height=dp(55),
            padding=dp(8),
            **kw
        )
        self.track = track
        self.idx = idx
        self.on_tap = on_tap
        self.selected = False
        
        with self.canvas.before:
            Color(*C['bg_light'])
            self.bg = Rectangle(pos=self.pos, size=self.size)
        
        self.bind(pos=self._upd, size=self._upd)
        
        self.add_widget(Label(
            text=track.display_name,
            color=C['text'],
            font_size=sp(14),
            halign='left',
            valign='middle',
            size_hint_y=0.6
        ))
        
        self.add_widget(Label(
            text=f"[{track.duration_str}]" if track.duration > 0 else "",
            color=C['text_dim'],
            font_size=sp(11),
            halign='left',
            size_hint_y=0.4
        ))
    
    def _upd(self, *a):
        self.bg.pos = self.pos
        self.bg.size = self.size
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if touch.is_double_tap:
                self.on_tap(self.idx)
            return True
        return super().on_touch_down(touch)
    
    def set_sel(self, s):
        self.selected = s
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*(C['primary'] if s else C['bg_light']))
            self.bg = Rectangle(pos=self.pos, size=self.size)


class Btn(Button):
    """Styled button"""
    def __init__(self, txt, primary=False, **kw):
        super().__init__(text=txt, **kw)
        self.background_normal = ''
        self.background_down = ''
        self.font_size = sp(14)
        self.bold = True
        self.is_primary = primary
        self._set_color()
    
    def _set_color(self):
        if self.is_primary:
            self.background_color = C['primary']
            self.color = C['white']
        else:
            self.background_color = C['bg_light']
            self.color = C['text']
    
    def set_active(self, a):
        if a:
            self.background_color = C['primary']
            self.color = C['white']
        else:
            self._set_color()


class RedAmpApp(App):
    """Main application"""
    state_txt = StringProperty("[STOP]")
    title_txt = StringProperty("No Track")
    time_cur = StringProperty("0:00")
    time_tot = StringProperty("0:00")
    vol_txt = StringProperty("70%")
    count_txt = StringProperty("0 tracks")
    
    def build(self):
        Window.clearcolor = C['bg']
        self.player = Player()
        self.track_widgets = []
        
        root = BoxLayout(orientation='vertical')
        
        # Header
        header = BoxLayout(size_hint_y=None, height=dp(48), padding=[dp(12), dp(6)])
        with header.canvas.before:
            Color(*C['bg_dark'])
            self.hdr_bg = Rectangle(pos=header.pos, size=header.size)
        header.bind(
            pos=lambda *a: setattr(self.hdr_bg, 'pos', header.pos),
            size=lambda *a: setattr(self.hdr_bg, 'size', header.size)
        )
        
        header.add_widget(Label(
            text="[RED-AMP] v1.3",
            color=C['primary'],
            font_size=sp(17),
            bold=True,
            halign='left'
        ))
        
        set_btn = Btn("[*]", size_hint=(None, None), size=(dp(42), dp(34)))
        set_btn.bind(on_release=self.show_settings)
        header.add_widget(set_btn)
        root.add_widget(header)
        
        # Content
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(6))
        
        # Visualizer
        self.viz = Visualizer()
        content.add_widget(self.viz)
        
        # State
        self.state_lbl = Label(
            text=self.state_txt,
            color=C['text_dim'],
            font_size=sp(11),
            size_hint_y=None,
            height=dp(18)
        )
        content.add_widget(self.state_lbl)
        
        # Title
        self.title_lbl = Label(
            text=self.title_txt,
            color=C['white'],
            font_size=sp(15),
            bold=True,
            size_hint_y=None,
            height=dp(24)
        )
        content.add_widget(self.title_lbl)
        
        # Artist
        self.artist_lbl = Label(
            text="",
            color=C['primary_light'],
            font_size=sp(13),
            size_hint_y=None,
            height=dp(20)
        )
        content.add_widget(self.artist_lbl)
        
        # Progress
        prog = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        
        self.time_cur_lbl = Label(
            text="0:00",
            color=C['primary_light'],
            font_size=sp(12),
            size_hint_x=None,
            width=dp(45)
        )
        
        self.slider = Slider(min=0, max=1000, value=0)
        self.slider.bind(on_touch_up=self._seek)
        
        self.time_tot_lbl = Label(
            text="0:00",
            color=C['primary_light'],
            font_size=sp(12),
            size_hint_x=None,
            width=dp(45)
        )
        
        prog.add_widget(self.time_cur_lbl)
        prog.add_widget(self.slider)
        prog.add_widget(self.time_tot_lbl)
        content.add_widget(prog)
        
        # Controls
        ctrl = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        ctrl.add_widget(BoxLayout())
        
        self.shuf_btn = Btn("[SHF]", size_hint=(None, None), size=(dp(52), dp(38)))
        self.shuf_btn.bind(on_release=self._shuf)
        ctrl.add_widget(self.shuf_btn)
        
        prev_btn = Btn("[<<]", primary=True, size_hint=(None, None), size=(dp(52), dp(38)))
        prev_btn.bind(on_release=lambda x: self.player.prev())
        ctrl.add_widget(prev_btn)
        
        self.play_btn = Btn("[>]", primary=True, size_hint=(None, None), size=(dp(52), dp(38)))
        self.play_btn.bind(on_release=lambda x: self.player.toggle())
        ctrl.add_widget(self.play_btn)
        
        next_btn = Btn("[>>]", primary=True, size_hint=(None, None), size=(dp(52), dp(38)))
        next_btn.bind(on_release=lambda x: self.player.next())
        ctrl.add_widget(next_btn)
        
        self.rpt_btn = Btn("[RPT]", size_hint=(None, None), size=(dp(52), dp(38)))
        self.rpt_btn.bind(on_release=self._rpt)
        ctrl.add_widget(self.rpt_btn)
        
        ctrl.add_widget(BoxLayout())
        content.add_widget(ctrl)
        
        # Volume
        vol = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        vol.add_widget(Label(text="[VOL]", color=C['text_dim'], size_hint_x=None, width=dp(42)))
        
        self.vol_slider = Slider(min=0, max=100, value=70, size_hint_x=0.45)
        self.vol_slider.bind(value=self._vol)
        vol.add_widget(self.vol_slider)
        
        self.vol_lbl = Label(text="70%", color=C['text_dim'], size_hint_x=None, width=dp(40))
        vol.add_widget(self.vol_lbl)
        vol.add_widget(BoxLayout())
        
        scan_btn = Btn("[SCAN]", size_hint=(None, None), size=(dp(65), dp(32)))
        scan_btn.bind(on_release=self._scan_popup)
        vol.add_widget(scan_btn)
        content.add_widget(vol)
        
        # Playlist header
        pl_hdr = BoxLayout(size_hint_y=None, height=dp(22))
        pl_hdr.add_widget(Label(
            text="[LIST]",
            color=C['primary_light'],
            font_size=sp(12),
            halign='left'
        ))
        
        self.cnt_lbl = Label(
            text="0 tracks",
            color=C['text_dim'],
            font_size=sp(11),
            halign='right'
        )
        pl_hdr.add_widget(self.cnt_lbl)
        content.add_widget(pl_hdr)
        
        # Playlist
        scroll = ScrollView()
        self.pl_box = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(2)
        )
        self.pl_box.bind(minimum_height=self.pl_box.setter('height'))
        scroll.add_widget(self.pl_box)
        content.add_widget(scroll)
        
        # Progress bar
        self.prog_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(6))
        self.prog_bar.opacity = 0
        content.add_widget(self.prog_bar)
        
        root.add_widget(content)
        
        # Player callbacks
        self.player.on_track = self._on_track
        self.player.on_state = self._on_state
        self.player.on_pos = self._on_pos
        
        Clock.schedule_once(lambda dt: self._load_saved(), 0.5)
        
        return root
    
    def _on_track(self, t):
        self.title_lbl.text = t.title
        self.artist_lbl.text = t.artist
        m, s = divmod(int(t.duration), 60)
        self.time_tot_lbl.text = f"{m}:{s:02d}"
        
        for i, w in enumerate(self.track_widgets):
            w.set_sel(i == self.player.index)
    
    def _on_state(self, s):
        states = {'play': '[PLAY]', 'pause': '[PAUSE]', 'stop': '[STOP]'}
        self.state_lbl.text = states.get(s, '[???]')
        
        if s == 'play':
            self.play_btn.text = "[||]"
            self.viz.set_active(True)
        else:
            self.play_btn.text = "[>]"
            self.viz.set_active(False)
    
    def _on_pos(self, p):
        l = self.player.length
        if l > 0:
            self.slider.value = (p / l) * 1000
        m, s = divmod(int(p), 60)
        self.time_cur_lbl.text = f"{m}:{s:02d}"
    
    def _seek(self, slider, touch):
        if slider.collide_point(*touch.pos):
            pos = (slider.value / 1000) * self.player.length
            self.player.seek(pos)
    
    def _vol(self, slider, val):
        self.player.set_volume(val / 100)
        self.vol_lbl.text = f"{int(val)}%"
    
    def _shuf(self, *a):
        on = self.player.toggle_shuffle()
        self.shuf_btn.set_active(on)
    
    def _rpt(self, *a):
        mode = self.player.cycle_repeat()
        if mode == 'none':
            self.rpt_btn.text = "[RPT]"
            self.rpt_btn.set_active(False)
        elif mode == 'all':
            self.rpt_btn.text = "[RPT]"
            self.rpt_btn.set_active(True)
        else:
            self.rpt_btn.text = "[RP1]"
            self.rpt_btn.set_active(True)
    
    def _scan_popup(self, *a):
        if platform == 'android':
            start = primary_external_storage_path()
        else:
            start = os.path.expanduser('~')
        
        box = BoxLayout(orientation='vertical', spacing=dp(8))
        fc = FileChooserListView(path=start, dirselect=True)
        box.add_widget(fc)
        
        btns = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8))
        popup = Popup(title="Select Folder", content=box, size_hint=(0.95, 0.85))
        
        def do_scan(*a):
            folder = fc.selection[0] if fc.selection else fc.path
            popup.dismiss()
            self._do_scan(folder)
        
        ok_btn = Btn("[SCAN]", primary=True)
        ok_btn.bind(on_release=do_scan)
        cancel_btn = Btn("[X]")
        cancel_btn.bind(on_release=popup.dismiss)
        
        btns.add_widget(ok_btn)
        btns.add_widget(cancel_btn)
        box.add_widget(btns)
        
        popup.open()
    
    def _do_scan(self, folder):
        self.prog_bar.opacity = 1
        self.prog_bar.value = 0
        
        import threading
        
        def scan():
            tracks = self.player.scan(
                folder,
                lambda n: Clock.schedule_once(
                    lambda dt: setattr(self.prog_bar, 'value', min(n, 100))
                )
            )
            Clock.schedule_once(lambda dt: self._scan_done(tracks))
        
        threading.Thread(target=scan, daemon=True).start()
    
    def _scan_done(self, tracks):
        self.player.set_tracks(tracks)
        self._update_list()
        self._save()
        self.prog_bar.opacity = 0
        self.cnt_lbl.text = f"{len(tracks)} tracks"
    
    def _update_list(self):
        self.pl_box.clear_widgets()
        self.track_widgets = []
        
        for i, t in enumerate(self.player.tracks):
            w = TrackRow(t, i, lambda idx: self.player.play(idx))
            self.pl_box.add_widget(w)
            self.track_widgets.append(w)
    
    def show_settings(self, *a):
        box = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(12))
        
        box.add_widget(Label(
            text="Red-Amp Settings v1.3",
            color=C['primary'],
            font_size=sp(16),
            size_hint_y=None,
            height=dp(30)
        ))
        
        row1 = BoxLayout(size_hint_y=None, height=dp(35))
        row1.add_widget(Label(text="Visualizer:", color=C['text']))
        self.viz_chk = CheckBox(active=self.viz.height > 10)
        row1.add_widget(self.viz_chk)
        box.add_widget(row1)
        
        box.add_widget(BoxLayout())
        
        btns = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(10))
        popup = Popup(title="Settings", content=box, size_hint=(0.85, 0.5))
        
        def save(*a):
            if self.viz_chk.active:
                self.viz.height = dp(70)
                self.viz.opacity = 1
            else:
                self.viz.height = dp(0)
                self.viz.opacity = 0
            popup.dismiss()
        
        ok_btn = Btn("[SAVE]", primary=True)
        ok_btn.bind(on_release=save)
        x_btn = Btn("[X]")
        x_btn.bind(on_release=popup.dismiss)
        
        btns.add_widget(ok_btn)
        btns.add_widget(x_btn)
        box.add_widget(btns)
        
        popup.open()
    
    def _get_save_path(self):
        if platform == 'android':
            return os.path.join(app_storage_path(), 'playlist.json')
        return os.path.expanduser('~/.redamp_playlist.json')
    
    def _save(self):
        try:
            data = [t.to_dict() for t in self.player.tracks]
            path = self._get_save_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def _load_saved(self):
        try:
            path = self._get_save_path()
            if os.path.exists(path):
                with open(path) as f:
                    data = json.load(f)
                tracks = [
                    Track.from_dict(d)
                    for d in data
                    if os.path.exists(d['path'])
                ]
                self.player.set_tracks(tracks)
                self._update_list()
                self.cnt_lbl.text = f"{len(tracks)} tracks"
        except:
            pass
    
    def on_stop(self):
        self._save()
        self.player.cleanup()


if __name__ == '__main__':
    RedAmpApp().run()

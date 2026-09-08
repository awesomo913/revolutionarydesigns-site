"""Install Journey presentation before game imports."""
from journey_art import image as _image, panda_frames, tile as platform_tile, cell

def _panda_cells():
    return [cell('panda-journey.png',4,3,i) for i in range(12)]

def install():
    import sprites
    import backgrounds
    import ui
    import journey_ui as theme
    from journey_art import PaintedBackground
    if getattr(sprites,'_painted_art_installed',False): return
    sprites._painted_art_installed=True
    sprites.generate_panda_frames=panda_frames
    backgrounds.BiomeBackground=PaintedBackground
    ui.get_font=theme.font
    ui.TitleScreen=theme.JourneyMenu
    ui.PauseOverlay=lambda: theme.JourneyMenu(paused=True)
    ui.HUD.draw=theme.hud_draw
    ui.GameOverScreen=theme.EndScreen
    ui.VictoryScreen=theme.VictoryScreen
    ui.LevelTransition=theme.LevelTransition
    boss=next(c for c in ui._CHARACTERS if c['key']=='boss')
    boss['story']='The fallen guardian charges across the lair. Watch the warning above its head and move out of the charge. After the charge, its blue stun state is your opening.\n\nHOW TO BEAT: Stomp only while it is stunned. Contact at any other time knocks you back and deals damage. Five clean hits defeat it and unlock ice magic.'
    for char in ui._CHARACTERS:
        char['story']=char['story'].replace('contact is lethal acid','contact deals damage').replace('or duck by sliding on ice','or jump over them').replace('freeze it with the ice spell','shatter it with the ice spell')
        if char['key']=='glow':
            char['story']='A cave creature that lures you close with a gentle green glow. It snaps when you enter its reach. Watch for the warm warning color.\n\nHOW TO BEAT: Keep your distance or use a staff or throwing star. It cannot be stomped.'
        if char['key']=='phantom':
            char['story']='A translucent spirit drifting across the salt flats. Watch its pale silhouette against the mountains and keep room to jump.\n\nHOW TO BEAT: Stomp from above or strike with the bamboo staff. Faint does not mean harmless.'
        if char['key'] in ('dust','brine'):
            char['story']+='\n\nICE: Once unlocked, ice magic can shatter this hazard.'

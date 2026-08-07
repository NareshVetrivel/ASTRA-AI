"""
ASTRA-AI
ui/styles/theme.py

Premium IEEE Light Theme
"""


# ==========================================================
# COLORS
# ==========================================================

PRIMARY = "#7C3AED"
PRIMARY_DARK = "#6D28D9"
PRIMARY_LIGHT = "#A855F7"

SECONDARY = "#3B82F6"

SUCCESS = "#16A34A"
WARNING = "#F59E0B"
DANGER = "#EF4444"

TEXT = "#1E293B"
TEXT_LIGHT = "#64748B"

BACKGROUND = "#F4F1FF"

CARD = "rgba(255,255,255,0.82)"
GLASS = "rgba(255,255,255,0.62)"
BORDER = "rgba(255,255,255,0.88)"

RADIUS = 26
CARD_RADIUS = 22
BUTTON_RADIUS = 26


GLOBAL_STYLE = f"""

/* ======================================================
   ASTRA PREMIUM BACKGROUND
====================================================== */

QMainWindow
{{
    background:qradialgradient(

        cx:0.50,
        cy:0.42,
        radius:1.35,

        stop:0      #FFFFFF,
        stop:0.18   #F8F5FF,
        stop:0.35   #F1ECFF,
        stop:0.55   #ECE6FF,
        stop:0.75   #F4F1FF,
        stop:1      #FBFAFF
    );

    color:{TEXT};

    font-family:
        "Segoe UI",
        "Poppins",
        Arial;

    font-size:14px;
}}

QWidget
{{
    background:transparent;
    color:{TEXT};
}}

QFrame
{{
    background:transparent;
    border:none;
}}

QLabel
{{
    background:transparent;
    color:{TEXT};
}}

QScrollArea,
QAbstractScrollArea
{{
    background:transparent;
    border:none;
}}

QPushButton
{{
    background:rgba(255,255,255,.92);

    border:1px solid rgba(255,255,255,.95);

    border-radius:{BUTTON_RADIUS}px;

    padding:10px 18px;

    font-size:14px;

    font-weight:600;
}}

QPushButton:hover
{{
    background:white;

    border:1px solid rgba(196,181,253,.75);
}}

QPushButton:pressed
{{
    background:#EEE7FF;
}}

QLineEdit
{{
    background:rgba(255,255,255,.96);

    border:1px solid #E5DEFF;

    border-radius:18px;

    padding:10px 16px;
}}

QScrollBar:vertical
{{
    width:8px;
    background:transparent;
}}

QScrollBar::handle:vertical
{{
    background:#D8CCFF;
    border-radius:4px;
}}

QScrollBar::handle:vertical:hover
{{
    background:#BFA9FF;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical
{{
    height:0px;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical
{{
    background:transparent;
}}

"""

# ==========================================================
# HEADER STYLE
# ==========================================================

HEADER_STYLE = """

#headerWidget
{
    background:qlineargradient(
        x1:0,
        y1:0,
        x2:1,
        y2:0,

        stop:0 rgba(255,255,255,.92),
        stop:0.35 rgba(250,247,255,.88),
        stop:0.70 rgba(245,241,255,.86),
        stop:1 rgba(255,255,255,.90)
    );

    border:1px solid rgba(255,255,255,.96);

    border-radius:30px;
}

#appTitle
{
    color:#1F2A72;

    font-size:24px;

    font-weight:800;
}

#appSubtitle
{
    color:#667085;

    font-size:11px;

    font-weight:600;

    letter-spacing:.8px;
}

#greetingLabel
{
    color:#172033;

    font-size:19px;

    font-weight:800;
}

#questionLabel
{
    color:#475467;

    font-size:13px;
}

#infoChip
{
    background:rgba(255,255,255,.86);

    border:1px solid rgba(255,255,255,.96);

    border-radius:18px;

    padding:8px 18px;
}

#powerButton
{
    background:white;

    border:2px solid rgba(255,90,90,.18);

    border-radius:28px;

    color:#EF4444;

    min-width:58px;
    max-width:58px;

    min-height:58px;
    max-height:58px;
}

#powerButton:hover
{
    background:#FFF4F4;

    border:2px solid #EF4444;
}

#powerButton:pressed
{
    background:#FFECEC;
}

"""

# ==========================================================
# FLOATING PANEL STYLE
# ==========================================================

PANEL_STYLE = """

#leftPanel,
#rightPanel
{
    background:transparent;
    border:none;
}

#leftTitle,
#rightTitle
{
    color:#6D28D9;

    font-size:20px;

    font-weight:800;

    padding-left:6px;

    letter-spacing:.8px;
}

#leftContainer,
#rightContainer
{
    background:transparent;
}

/* Floating Effect */

QFrame#GlassCard,
QFrame#StatusTile,
QFrame#MetricTile
{
    background:qlineargradient(
        x1:0,
        y1:0,
        x2:1,
        y2:1,

        stop:0 rgba(255,255,255,.95),
        stop:1 rgba(248,244,255,.88)
    );

    border:1px solid rgba(255,255,255,.95);

    border-radius:22px;
}

"""


# ==========================================================
# STATUS CARD STYLE
# ==========================================================

STATUS_CARD_STYLE = """

QFrame#StatusTile,
QFrame#StatusCard
{
    background:qlineargradient(
        x1:0,
        y1:0,
        x2:1,
        y2:1,

        stop:0 rgba(255,255,255,.96),
        stop:0.45 rgba(251,249,255,.93),
        stop:1 rgba(245,241,255,.88)
    );

    border:1px solid rgba(255,255,255,.96);

    border-radius:22px;
}

QFrame#StatusTile:hover,
QFrame#StatusCard:hover
{
    background:white;

    border:1px solid rgba(196,181,253,.70);
}

#cardTitle
{
    color:#172033;

    font-size:16px;

    font-weight:800;
}

#cardSubtitle
{
    color:#667085;

    font-size:12px;

    font-weight:500;
}

#statusValue
{
    color:#475467;

    font-size:13px;

    font-weight:800;
}

"""


# ==========================================================
# METRIC CARD STYLE
# ==========================================================

METRIC_CARD_STYLE = """

QFrame#MetricTile,
QFrame#MetricCard
{
    background:qlineargradient(
        x1:0,
        y1:0,
        x2:1,
        y2:1,

        stop:0 rgba(255,255,255,.96),
        stop:0.45 rgba(251,249,255,.93),
        stop:1 rgba(245,241,255,.88)
    );

    border:1px solid rgba(255,255,255,.96);

    border-radius:22px;
}

QFrame#MetricTile:hover,
QFrame#MetricCard:hover
{
    background:white;

    border:1px solid rgba(196,181,253,.70);
}

#metricTitle
{
    color:#172033;

    font-size:15px;

    font-weight:800;
}

#metricSubtitle
{
    color:#667085;

    font-size:11px;

    font-weight:500;
}

#metricValue
{
    font-size:18px;

    font-weight:800;
}

"""


# ==========================================================
# STATUS COLORS
# ==========================================================

STATUS_STYLE = """

#statusGreen
{
    color:#16A34A;
}

#statusBlue
{
    color:#2563EB;
}

#statusPurple
{
    color:#7C3AED;
}

#statusOrange
{
    color:#EA580C;
}

#statusRed
{
    color:#EF4444;
}

#statusGray
{
    color:#64748B;
}

#statusValue
{
    color:#64748B;

    font-size:11px;

    font-weight:700;
}

"""

# ==========================================================
# CENTER PANEL
# ==========================================================

CENTER_STYLE = """

#centerPanel
{
    background:transparent;
}

#heroContainer
{
    background:transparent;
}

#glowContainer
{
    background:transparent;
}

#avatarContainer
{
    background:transparent;
}

#avatarWidget
{
    background:transparent;
}

#ctaLabel,
#ctaButton
{
    background:rgba(255,255,255,.88);

    border:1px solid rgba(196,181,253,.55);

    border-radius:28px;

    padding:14px 36px;

    color:#6D28D9;

    font-size:15px;

    font-weight:800;
}

"""


# ==========================================================
# MICROPHONE
# ==========================================================

MIC_STYLE = """

#micButton
{
    background:qradialgradient(
        cx:0.5,
        cy:0.5,
        radius:0.95,

        stop:0 #DDD6FE,
        stop:0.30 #A78BFA,
        stop:0.70 #8B5CF6,
        stop:1 #5B21B6
    );

    color:white;

    border:8px solid rgba(255,255,255,.85);

    border-radius:75px;

    font-size:56px;

    font-weight:700;
}

#micButton:hover
{
    border:10px solid rgba(255,255,255,1);

    background:qradialgradient(
        cx:0.5,
        cy:0.5,
        radius:0.95,

        stop:0 #E9DDFF,
        stop:0.35 #B794FF,
        stop:0.75 #8B5CF6,
        stop:1 #6D28D9
    );
}

#micButton:pressed
{
    background:#6D28D9;
}

"""


# ==========================================================
# ICON CIRCLES
# ==========================================================

ICON_STYLE = """

#iconCirclePurple,
#iconCircleBlue,
#iconCircleGreen,
#iconCircleOrange,
#iconCirclePink
{
    border-radius:22px;
}

#iconCirclePurple{
    background:#F3E8FF;
    border:1px solid #DDD6FE;
}

#iconCircleBlue{
    background:#EFF6FF;
    border:1px solid #BFDBFE;
}

#iconCircleGreen{
    background:#ECFDF5;
    border:1px solid #BBF7D0;
}

#iconCircleOrange{
    background:#FFF7ED;
    border:1px solid #FED7AA;
}

#iconCirclePink{
    background:#FDF2F8;
    border:1px solid #FBCFE8;
}

"""


# ==========================================================
# TOOLTIP
# ==========================================================

TOOLTIP_STYLE = """

QToolTip
{
    background:white;

    color:#172033;

    border:1px solid rgba(196,181,253,.85);

    border-radius:12px;

    padding:8px 12px;

    font-size:12px;
}

"""


# ==========================================================
# DISABLED
# ==========================================================

DISABLED_STYLE = """

QPushButton:disabled,
QLabel:disabled,
QFrame:disabled
{
    color:#94A3B8;

    opacity:.55;
}

"""

class Theme:

    @staticmethod
    def get_stylesheet():

        return (
            GLOBAL_STYLE
            + HEADER_STYLE
            + PANEL_STYLE
            + STATUS_CARD_STYLE
            + METRIC_CARD_STYLE
            + STATUS_STYLE
            + CENTER_STYLE
            + MIC_STYLE
            + ICON_STYLE
            + TOOLTIP_STYLE
            + DISABLED_STYLE
        )
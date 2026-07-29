#!/usr/bin/env python3
"""Build the final, visually verified HCI DA1 Word report."""

from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

from build_assignment_report import (
    ACCENT_FILL,
    BLUE,
    CONTENT_WIDTH_DXA,
    DARK_BLUE,
    HEADER_FILL,
    INK,
    MUTED,
    REFERENCES as VOICE_REFERENCES,
    add_bullets,
    add_caption,
    add_field,
    add_heading,
    add_hyperlink,
    add_section_intro,
    add_steps,
    add_text,
    apply_numbering,
    create_numbering,
    font,
    repeat_table_header,
    set_cell_shading,
    set_header_footer,
    set_repeatable_cell_text,
    set_run_font,
    set_table_geometry,
    style_document,
)


ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "assets"
OUTPUT_PATH = ROOT / "HCI_DA1_Final_Multimodal_Hands_Free_Interface.docx"
ARCHITECTURE_PATH = ASSETS_DIR / "multimodal_system_architecture.png"
TONGUE_PATH = ASSETS_DIR / "tongue_click_state_machine.png"
METHODOLOGY_PATH = ASSETS_DIR / "finalized_methodology_workflow.png"
HARDWARE_PATH = ASSETS_DIR / "hardware_setup_schematic.png"


PAPERS = [
    {
        "theme": "Speech HCI review",
        "citation": "Clark et al. (2019)",
        "review": (
            "Maps 99 empirical speech-HCI papers and identifies accessibility, "
            "interaction design, evaluation, and deployment as major themes. It "
            "shows that recognition accuracy alone is insufficient and motivates "
            "the present combination of action feedback, safety states, fallback "
            "input, and task-based evaluation."
        ),
    },
    {
        "theme": "VUI systematic review",
        "citation": "Deshmukh and Chalmeta (2024)",
        "review": (
            "Synthesizes 125 voice-interface studies and highlights recurring gaps "
            "in error recovery, inclusion, context, user diversity, and comparable "
            "usability measures. The project responds with a constrained command "
            "set, explicit status messages, exact matching, and repeatable logs."
        ),
    },
    {
        "theme": "Usability review",
        "citation": "Dutsinma et al. (2022)",
        "review": (
            "Organizes voice-assistant usability through ISO 9241-11 effectiveness, "
            "efficiency, and satisfaction. Because prior studies measure these "
            "dimensions inconsistently, the finalized method combines recognition "
            "accuracy, task completion, response time, errors, and user ratings."
        ),
    },
    {
        "theme": "Voice pointing",
        "citation": "Harada et al. (2006)",
        "review": (
            "Introduces Vocal Joystick, mapping vocal parameters to continuous "
            "pointer movement and evaluating the speed-accuracy relationship. It "
            "is the closest voice-cursor precedent; the present implementation uses "
            "simpler discrete commands while head/eye control supplies continuity."
        ),
    },
    {
        "theme": "Assistive voice pointing",
        "citation": "Harada et al. (2009)",
        "review": (
            "A longitudinal study with motor-impaired and non-impaired participants "
            "demonstrates learning effects in continuous voice cursor control. It "
            "supports including practice trials and avoiding conclusions based only "
            "on a first-use measurement."
        ),
    },
    {
        "theme": "Low-cost multimodal access",
        "citation": "Ramos et al. (2022)",
        "review": (
            "Presents EMKEY, combining facial landmarks with voice commands for "
            "mouse and keyboard emulation using ordinary consumer hardware. This is "
            "the closest whole-system precedent and validates the project's laptop "
            "camera, microphone, and software-only design."
        ),
    },
    {
        "theme": "Accessible VUI design",
        "citation": "Corbett and Weber (2016)",
        "review": (
            "Studies a completely hands-free VUI for people with limited hand "
            "dexterity and identifies discoverability and command learning as major "
            "challenges. The implemented GUI therefore keeps supported commands, "
            "recognizer state, transcript, and result feedback visible."
        ),
    },
    {
        "theme": "Input comparison",
        "citation": "Bekker et al. (1995)",
        "review": (
            "Compares mouse and speech control in a text-annotation task and shows "
            "that preferences vary when both modalities are available. The result "
            "supports treating voice and camera control as alternatives while "
            "retaining the physical mouse/trackpad as a safety fallback."
        ),
    },
    {
        "theme": "Speech accessibility",
        "citation": "Young and Mihailidis (2010)",
        "review": (
            "Reviews recognition difficulties for dysarthric speakers and the "
            "implications for older users. It limits any claim of universal access "
            "and motivates reporting participant speech characteristics, errors, "
            "and model limitations rather than only average accuracy."
        ),
    },
    {
        "theme": "Disability and ASR",
        "citation": "Berner and Alves (2023)",
        "review": (
            "A scoping review finds potential participation and independence "
            "benefits from speech recognition but relatively limited empirical "
            "evidence across disability contexts. The project is therefore framed "
            "as a research prototype requiring target-user validation."
        ),
    },
    {
        "theme": "ALS and ASR",
        "citation": "Cave and Bloch (2023)",
        "review": (
            "Reviews ASR use by people living with ALS and relates performance to "
            "dysarthria severity and technology choice. It demonstrates why word "
            "recognition and functional task success must be measured separately."
        ),
    },
    {
        "theme": "Speech evaluation",
        "citation": "Hone and Graham (2000)",
        "review": (
            "Develops the SASSI questionnaire and identifies response accuracy, "
            "likeability, cognitive demand, annoyance, habitability, and speed as "
            "subjective factors. These constructs form the proposed post-task "
            "questionnaire rather than an unvalidated satisfaction question."
        ),
    },
    {
        "theme": "Expectation gap",
        "citation": "Luger and Sellen (2016)",
        "review": (
            "Finds a gulf between users' expectations and the actual capabilities "
            "of conversational agents. The prototype is deliberately described as "
            "a command interface, not a conversational assistant, and exposes its "
            "supported vocabulary."
        ),
    },
    {
        "theme": "Privacy and use",
        "citation": "Cowan et al. (2017)",
        "review": (
            "Reports frustration with incomplete hands-free interaction as well as "
            "privacy, transparency, and social concerns. Local Parakeet/Vosk "
            "recognition, non-retention of raw audio, visible mode indicators, and "
            "multiple input channels directly address these concerns."
        ),
    },
    {
        "theme": "ASR fairness",
        "citation": "Koenecke et al. (2020)",
        "review": (
            "Demonstrates substantial racial disparities across five commercial ASR "
            "systems. The study makes diverse accents and speaker backgrounds a "
            "methodological requirement and prevents a single-user development run "
            "from being presented as general recognition accuracy."
        ),
    },
    {
        "theme": "Error correction",
        "citation": "Suhm et al. (2001)",
        "review": (
            "Shows that users benefit from switching modalities when correcting "
            "speech-recognition errors. This supports the project's multimodal "
            "recovery strategy: users may use voice, head/eye movement, tongue "
            "clicks, GUI buttons, or the physical input device."
        ),
    },
    {
        "theme": "Eye-gaze foundations",
        "citation": "Jacob (1991)",
        "review": (
            "Establishes foundational eye-movement interaction techniques and the "
            "difficulty of interpreting natural looking as intentional input. This "
            "is the conceptual basis for separating gaze-based cursor movement from "
            "tongue-based click confirmation."
        ),
    },
    {
        "theme": "Gaze selection",
        "citation": "Sibert and Jacob (2000)",
        "review": (
            "Empirically evaluates eye-gaze interaction for target selection. The "
            "work demonstrates the speed potential of gaze while exposing accuracy "
            "and calibration constraints; the implementation therefore adds "
            "smoothing, a dead zone, recalibration, and a separate click gesture."
        ),
    },
    {
        "theme": "Hybrid gaze pointing",
        "citation": "Zhai et al. (1999)",
        "review": (
            "MAGIC pointing cascades gaze with manual control to reduce pointer "
            "travel without making gaze alone responsible for selection. It supports "
            "the project's division of labor: camera movement brings the pointer "
            "near a target and tongue/voice performs the deliberate action."
        ),
    },
    {
        "theme": "Eye typing review",
        "citation": "Majaranta and Räihä (2002)",
        "review": (
            "Reviews two decades of eye typing, including dwell time, feedback, "
            "calibration, and the Midas-touch problem. These findings motivate "
            "explicit calibration, visible feedback, and avoidance of automatic "
            "gaze-only clicking."
        ),
    },
    {
        "theme": "Gaze performance",
        "citation": "Vertegaal (2008)",
        "review": (
            "Uses Fitts' law to compare eye tracking with manual target selection. "
            "It provides an established basis for measuring speed and target-size "
            "effects, informing the proposed pointing and selection tasks."
        ),
    },
    {
        "theme": "Webcam head control",
        "citation": "Betke et al. (2002)",
        "review": (
            "The Camera Mouse tracks visible body features to provide computer "
            "access for people with severe disabilities. It demonstrates that "
            "camera-based pointer control can avoid wearable hardware and directly "
            "supports the built-in-webcam approach."
        ),
    },
    {
        "theme": "Head-control ergonomics",
        "citation": "LoPresti et al. (2002)",
        "review": (
            "Compares head-operated control methods for participants with and "
            "without disabilities. Its performance and control-method emphasis "
            "motivates adjustable gain, dead zones, calibration, and separate "
            "analysis of movement time and selection accuracy."
        ),
    },
    {
        "theme": "Adaptive head control",
        "citation": "LoPresti and Brienza (2004)",
        "review": (
            "Investigates adaptive software for head-operated controls. The result "
            "supports user-specific neutral-position calibration and future "
            "personalization of gain rather than assuming one sensitivity works for "
            "every user."
        ),
    },
    {
        "theme": "Visual face tracking",
        "citation": "Tu et al. (2007)",
        "review": (
            "Maps visual face tracking to mouse control and provides an algorithmic "
            "precedent for camera-only pointing. The present system applies the same "
            "principle through modern dense face landmarks and relative motion."
        ),
    },
    {
        "theme": "Facial landmarks",
        "citation": "Baltrušaitis et al. (2018)",
        "review": (
            "Presents OpenFace 2.0 for facial landmarks, head pose, gaze, and facial "
            "behavior analysis. Although the implementation uses MediaPipe, this "
            "work validates the broader landmark-based pipeline and highlights the "
            "importance of robust tracking under real-world variation."
        ),
    },
    {
        "theme": "Tongue interface",
        "citation": "Huo and Ghovanloo (2012)",
        "review": (
            "Describes Tongue Drive as an assistive channel for people with severe "
            "motor disability. It establishes the tongue as a purposeful, high-"
            "availability control modality, while the present project explores a "
            "non-contact webcam alternative instead of magnetic hardware."
        ),
    },
    {
        "theme": "Tongue sensing",
        "citation": "Huo et al. (2008)",
        "review": (
            "Develops a magneto-inductive tongue-computer interface and demonstrates "
            "multi-command tongue input. It informs the mapping from deliberate "
            "tongue gestures to discrete commands but also shows the hardware burden "
            "avoided by calibrated computer vision."
        ),
    },
    {
        "theme": "Tongue evaluation",
        "citation": "Huo (2008)",
        "review": (
            "Reports a preliminary evaluation of the Tongue Drive System with people "
            "having little or no upper-limb function. It supports functional task "
            "testing and user-specific calibration rather than evaluating gesture "
            "classification in isolation."
        ),
    },
    {
        "theme": "Multimodal HCI",
        "citation": "Oviatt et al. (2004)",
        "review": (
            "Shows that multimodal behavior increases as task and cognitive load "
            "rise. The project therefore does not force one modality: voice can "
            "invoke named actions, head/eye controls movement, and tongue supplies "
            "intentional clicking."
        ),
    },
]


REFERENCES = [
    *[
        VOICE_REFERENCES[index]
        for index in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 14, 15, 16, 27, 13)
    ],
    (
        "R. J. K. Jacob, \"The Use of Eye Movements in Human-Computer "
        "Interaction Techniques,\" ACM Transactions on Information Systems, "
        "vol. 9, no. 2, pp. 152-169, 1991. ",
        "10.1145/123078.128728",
    ),
    (
        "L. E. Sibert and R. J. K. Jacob, \"Evaluation of Eye Gaze "
        "Interaction,\" in Proceedings of CHI 2000, pp. 281-288, 2000. ",
        "10.1145/332040.332445",
    ),
    (
        "S. Zhai, C. Morimoto, and S. Ihde, \"Manual and Gaze Input Cascaded "
        "(MAGIC) Pointing,\" in Proceedings of CHI '99, pp. 246-253, 1999. ",
        "10.1145/302979.303053",
    ),
    (
        "P. Majaranta and K.-J. Räihä, \"Twenty Years of Eye Typing: Systems "
        "and Design Issues,\" in Proceedings of ETRA '02, pp. 15-22, 2002. ",
        "10.1145/507072.507076",
    ),
    (
        "R. Vertegaal, \"A Fitts Law Comparison of Eye Tracking and Manual "
        "Input in the Selection of Visual Targets,\" in Proceedings of ICMI "
        "2008, pp. 241-248, 2008. ",
        "10.1145/1452392.1452443",
    ),
    (
        "M. Betke, J. Gips, and P. Fleming, \"The Camera Mouse: Visual Tracking "
        "of Body Features to Provide Computer Access for People with Severe "
        "Disabilities,\" IEEE Transactions on Neural Systems and Rehabilitation "
        "Engineering, vol. 10, no. 1, pp. 1-10, 2002. ",
        "10.1109/TNSRE.2002.1021581",
    ),
    (
        "E. F. LoPresti, D. M. Brienza, and J. Angelo, \"Head-Operated Computer "
        "Controls: Effect of Control Method on Performance for Subjects with "
        "and without Disability,\" Interacting with Computers, vol. 14, no. 4, "
        "pp. 359-377, 2002. ",
        "10.1016/S0953-5438(01)00058-3",
    ),
    (
        "E. F. LoPresti and D. M. Brienza, \"Adaptive Software for Head-"
        "Operated Computer Controls,\" IEEE Transactions on Neural Systems and "
        "Rehabilitation Engineering, vol. 12, no. 1, pp. 102-111, 2004. ",
        "10.1109/TNSRE.2003.822762",
    ),
    (
        "J. Tu, H. Tao, and T. Huang, \"Face as Mouse through Visual Face "
        "Tracking,\" Computer Vision and Image Understanding, vol. 108, "
        "nos. 1-2, pp. 35-40, 2007. ",
        "10.1016/j.cviu.2006.11.007",
    ),
    (
        "T. Baltrušaitis, A. Zadeh, Y. C. Lim, and L.-P. Morency, \"OpenFace "
        "2.0: Facial Behavior Analysis Toolkit,\" in 13th IEEE International "
        "Conference on Automatic Face & Gesture Recognition, pp. 59-66, 2018. ",
        "10.1109/FG.2018.00019",
    ),
    (
        "X. Huo and M. Ghovanloo, \"Tongue Drive: A Wireless Tongue-Operated "
        "Means for People with Severe Disabilities to Communicate Their "
        "Intentions,\" IEEE Communications Magazine, vol. 50, no. 10, "
        "pp. 128-135, 2012. ",
        "10.1109/MCOM.2012.6316786",
    ),
    (
        "X. Huo, J. Wang, and M. Ghovanloo, \"A Magneto-Inductive Sensor Based "
        "Wireless Tongue-Computer Interface,\" IEEE Transactions on Neural "
        "Systems and Rehabilitation Engineering, vol. 16, no. 5, pp. 497-504, "
        "2008. ",
        "10.1109/TNSRE.2008.2003375",
    ),
    (
        "X. Huo, \"Introduction and Preliminary Evaluation of the Tongue Drive "
        "System: Wireless Tongue-Operated Assistive Technology for People with "
        "Little or No Upper-Limb Function,\" Journal of Rehabilitation Research "
        "and Development, vol. 45, no. 6, pp. 921-930, 2008. ",
        "10.1682/JRRD.2007.06.0096",
    ),
    (
        "S. Oviatt, R. Coulston, and R. Lunsford, \"When Do We Interact "
        "Multimodally? Cognitive Load and Multimodal Communication Patterns,\" "
        "in Proceedings of ICMI '04, pp. 129-136, 2004. ",
        "10.1145/1027933.1027957",
    ),
]


def wrapped(draw: ImageDraw.ImageDraw, text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(text, width=width))


def box(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    title: str,
    body: str,
    *,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] = (46, 116, 181),
    title_size: int = 27,
    body_size: int = 22,
) -> None:
    left, top, right, bottom = xy
    draw.rounded_rectangle(
        xy,
        radius=22,
        fill=fill,
        outline=outline,
        width=4,
    )
    draw.text(
        ((left + right) // 2, top + 38),
        title,
        font=font(title_size, bold=True),
        fill=(31, 77, 120),
        anchor="mm",
    )
    draw.multiline_text(
        ((left + right) // 2, top + 94),
        wrapped(draw, body, max(17, (right - left) // 14)),
        font=font(body_size),
        fill=(46, 50, 54),
        anchor="ma",
        align="center",
        spacing=7,
    )


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    color: tuple[int, int, int] = (46, 116, 181),
    width: int = 7,
) -> None:
    draw.line((start, end), fill=color, width=width)
    x, y = end
    if abs(end[0] - start[0]) >= abs(end[1] - start[1]):
        points = [(x, y), (x - 20, y - 13), (x - 20, y + 13)]
    else:
        points = [(x, y), (x - 13, y - 20), (x + 13, y - 20)]
    draw.polygon(points, fill=color)


def create_architecture() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (2000, 1230), "white")
    draw = ImageDraw.Draw(image)
    draw.text(
        (1000, 50),
        "Implemented multimodal hands-free architecture",
        font=font(43, bold=True),
        fill=(32, 55, 72),
        anchor="ma",
    )
    draw.text(
        (1000, 108),
        "All inference and control run locally on the MacBook",
        font=font(24),
        fill=(90, 100, 110),
        anchor="ma",
    )

    rows = [
        (
            180,
            "VOICE",
            ("Microphone +\nisolated worker", "Adaptive VAD\nutterance segmentation"),
            ("MacParakeet\nTDT 0.6B v3", "Vosk offline\nfallback"),
            ("Exact command\nparser", "Movement, click,\nscroll, tabs"),
        ),
        (
            430,
            "CAMERA",
            ("FaceTime camera\n640 × 480", "Mirrored 24 fps\nvideo"),
            ("MediaPipe Face\nLandmarker", "Head, iris and\nmouth features"),
            ("Relative pointer\nmapper", "Head or gaze\nmovement"),
        ),
        (
            680,
            "TONGUE",
            ("Neutral + tongue\ncalibration", "User-specific\nfeature profiles"),
            ("Gesture state\nmachine", "Out/retract and\n0.7 s sequence"),
            ("Native click\nsequence", "Single, double or\ntriple click"),
        ),
        (
            930,
            "SCREEN TARGET",
            ("Spoken label", "e.g., click Projects"),
            ("AX semantic search\nthen OCR fallback", "Tesseract on\nvisible screen"),
            ("Exact target\nselection", "Ignore transcript\nand text fields"),
        ),
    ]
    for y, label, left_data, middle_data, right_data in rows:
        draw.text(
            (55, y + 91),
            label,
            font=font(23, bold=True),
            fill=(31, 77, 120),
            anchor="lm",
        )
        box(
            draw,
            (235, y, 645, y + 185),
            left_data[0],
            left_data[1],
            fill=(242, 246, 250),
        )
        box(
            draw,
            (745, y, 1155, y + 185),
            middle_data[0],
            middle_data[1],
            fill=(232, 238, 245),
        )
        box(
            draw,
            (1255, y, 1665, y + 185),
            right_data[0],
            right_data[1],
            fill=(242, 246, 250),
        )
        arrow(draw, (650, y + 92), (735, y + 92))
        arrow(draw, (1160, y + 92), (1245, y + 92))
        arrow(draw, (1670, y + 92), (1770, y + 92))

    draw.rounded_rectangle(
        (1770, 180, 1960, 1115),
        radius=24,
        fill=(255, 249, 231),
        outline=(192, 142, 37),
        width=5,
    )
    draw.multiline_text(
        (1865, 235),
        "SAFETY +\nACTION\nEXECUTOR",
        font=font(27, bold=True),
        fill=(122, 90, 0),
        anchor="ma",
        align="center",
        spacing=9,
    )
    safety = [
        "Enabled / paused gate",
        "Activate app below cursor",
        "Quartz multi-click states",
        "PyAutoGUI movement",
        "Click-through feedback ring",
        "CSV session log",
        "macOS Accessibility checks",
    ]
    draw.multiline_text(
        (1865, 430),
        "\n\n".join(wrapped(draw, item, 17) for item in safety),
        font=font(20),
        fill=(70, 65, 48),
        anchor="ma",
        align="center",
        spacing=4,
    )
    image.save(ARCHITECTURE_PATH, dpi=(180, 180))


def create_tongue_figure() -> None:
    image = Image.new("RGB", (1900, 920), "white")
    draw = ImageDraw.Draw(image)
    draw.text(
        (950, 48),
        "Calibrated tongue gesture and native click state machine",
        font=font(42, bold=True),
        fill=(32, 55, 72),
        anchor="ma",
    )
    items = [
        ("1  Neutral", "Mouth closed\n28 frames"),
        ("2  Tongue", "Tongue held out\n28 frames"),
        ("3  Armed", "Retract for\n5 frames"),
        ("4  Gesture", "Out ≥3 frames\nretract ≥3"),
        ("5  Aggregate", "Count complete\ngestures for 0.7 s"),
    ]
    start_x = 70
    y = 190
    width = 300
    gap = 70
    for index, (title, body) in enumerate(items):
        x = start_x + index * (width + gap)
        box(
            draw,
            (x, y, x + width, y + 220),
            title,
            body,
            fill=(232, 238, 245) if index < 3 else (242, 246, 250),
            title_size=25,
            body_size=22,
        )
        if index < len(items) - 1:
            arrow(draw, (x + width + 4, y + 110), (x + width + gap - 8, y + 110))

    branch_y = 590
    branches = [
        ("1 gesture", "Single click\nblue ring 1", (220, 514, 1000)),
        ("2 gestures", "Double click\norange ring 2", (242, 140, 36)),
        ("3 gestures", "Triple click\npurple ring 3", (176, 67, 219)),
    ]
    for index, (title, body, color) in enumerate(branches):
        x = 275 + index * 520
        draw.rounded_rectangle(
            (x, branch_y, x + 360, branch_y + 205),
            radius=24,
            fill=(250, 250, 252),
            outline=color,
            width=6,
        )
        draw.text(
            (x + 180, branch_y + 50),
            title,
            font=font(27, bold=True),
            fill=color,
            anchor="mm",
        )
        draw.multiline_text(
            (x + 180, branch_y + 105),
            body,
            font=font(22),
            fill=(45, 50, 55),
            anchor="ma",
            align="center",
            spacing=8,
        )
        draw.text(
            (x + 180, branch_y + 172),
            f"Quartz clickState 1{'–2' if index == 1 else '–3' if index == 2 else ''}",
            font=font(18, bold=True),
            fill=(90, 100, 110),
            anchor="mm",
        )
        arrow(draw, (950, y + 226), (x + 180, branch_y - 12), color=color, width=5)
    image.save(TONGUE_PATH, dpi=(180, 180))


def create_methodology_figure() -> None:
    image = Image.new("RGB", (1900, 940), "white")
    draw = ImageDraw.Draw(image)
    draw.text(
        (950, 48),
        "Finalized development and evaluation methodology",
        font=font(42, bold=True),
        fill=(32, 55, 72),
        anchor="ma",
    )
    stages = [
        ("1  Evidence", "30 DOI papers\nrequirements + risks"),
        ("2  Build", "Offline speech,\nvision and OS control"),
        ("3  Verify", "65 unit tests,\npermissions, dry run"),
        ("4  Pilot", "Quiet + noise,\nrandomized tasks"),
        ("5  Measure", "Accuracy, time,\nerrors, SASSI"),
        ("6  Analyze", "Paired results,\nmedian + Wilcoxon"),
    ]
    y = 210
    box_w = 250
    gap = 55
    total = len(stages) * box_w + (len(stages) - 1) * gap
    x0 = (1900 - total) // 2
    for index, (title, body) in enumerate(stages):
        x = x0 + index * (box_w + gap)
        box(
            draw,
            (x, y, x + box_w, y + 250),
            title,
            body,
            fill=(232, 238, 245) if index % 2 == 0 else (244, 246, 249),
            title_size=23,
            body_size=20,
        )
        if index < len(stages) - 1:
            arrow(draw, (x + box_w + 4, y + 125), (x + box_w + gap - 7, y + 125))

    draw.rounded_rectangle(
        (190, 590, 1710, 830),
        radius=24,
        fill=(255, 249, 231),
        outline=(192, 142, 37),
        width=4,
    )
    draw.text(
        (950, 635),
        "Acceptance criteria",
        font=font(29, bold=True),
        fill=(122, 90, 0),
        anchor="ma",
    )
    criteria = [
        "≥85% voice accuracy  •  median response ≤3 seconds",
        "≥80% target completion  •  ≥90% click-count accuracy",
        "Zero paused/evaluation actions  •  no destructive commands",
    ]
    draw.multiline_text(
        (950, 700),
        "\n".join(criteria),
        font=font(25, bold=True),
        fill=(70, 65, 48),
        anchor="ma",
        align="center",
        spacing=15,
    )
    image.save(METHODOLOGY_PATH, dpi=(180, 180))


def create_hardware_figure() -> None:
    image = Image.new("RGB", (1800, 920), "white")
    draw = ImageDraw.Draw(image)
    draw.text(
        (900, 45),
        "Minimal hardware configuration",
        font=font(42, bold=True),
        fill=(32, 55, 72),
        anchor="ma",
    )
    draw.rounded_rectangle(
        (500, 185, 1300, 735),
        radius=38,
        fill=(238, 241, 244),
        outline=(65, 75, 85),
        width=8,
    )
    draw.rounded_rectangle(
        (555, 235, 1245, 655),
        radius=16,
        fill=(217, 232, 244),
        outline=(46, 116, 181),
        width=5,
    )
    draw.ellipse((885, 202, 915, 232), fill=(35, 35, 35))
    draw.text(
        (900, 415),
        "Apple Silicon MacBook\nOne-device prototype",
        font=font(35, bold=True),
        fill=(32, 55, 72),
        anchor="mm",
        align="center",
        spacing=10,
    )
    draw.polygon(
        [(440, 735), (1360, 735), (1490, 805), (310, 805)],
        fill=(200, 205, 210),
        outline=(65, 75, 85),
    )
    labels = [
        ((160, 210), "Built-in camera", "Face, iris and tongue landmarks", (500, 260)),
        ((155, 500), "Built-in microphone", "Offline voice commands", (500, 560)),
        ((1380, 235), "Display", "Targets, transcript and feedback", (1245, 325)),
        ((1375, 540), "CPU + 8 GB RAM", "Parakeet, MediaPipe and OCR", (1245, 570)),
    ]
    for (x, y), title, body, target in labels:
        align = "la" if x < 900 else "ra"
        anchor_x = x + 300 if x < 900 else x - 300
        draw.text(
            (x, y),
            title,
            font=font(26, bold=True),
            fill=(31, 77, 120),
            anchor=align,
        )
        draw.multiline_text(
            (x, y + 42),
            wrapped(draw, body, 24),
            font=font(20),
            fill=(70, 75, 80),
            anchor=align,
            spacing=6,
        )
        draw.line((anchor_x, y + 28, target[0], target[1]), fill=(46, 116, 181), width=5)
    draw.text(
        (900, 875),
        "No eye tracker • no wearable tongue sensor • no external controller • no dedicated GPU",
        font=font(24, bold=True),
        fill=(90, 100, 110),
        anchor="mm",
    )
    image.save(HARDWARE_PATH, dpi=(180, 180))


def add_figure(doc: Document, path: Path, caption: str, alt_text: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.keep_with_next = True
    run = paragraph.add_run()
    inline = run.add_picture(str(path), width=Inches(6.35))
    inline._inline.docPr.set("descr", alt_text)
    add_caption(doc, caption)


def add_callout(doc: Document, label: str, text: str) -> None:
    """Add a shaded bordered paragraph without misusing a layout table."""
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.left_indent = Inches(0.08)
    paragraph.paragraph_format.right_indent = Inches(0.08)
    paragraph.paragraph_format.space_before = Pt(5)
    paragraph.paragraph_format.space_after = Pt(10)
    paragraph.paragraph_format.line_spacing = 1.15
    paragraph.paragraph_format.keep_together = True
    p_pr = paragraph._p.get_or_add_pPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), "F4F6F9")
    p_pr.append(shading)
    borders = OxmlElement("w:pBdr")
    for edge in ("top", "left", "bottom", "right"):
        border = OxmlElement(f"w:{edge}")
        border.set(qn("w:val"), "single")
        border.set(qn("w:sz"), "6")
        border.set(qn("w:space"), "6")
        border.set(qn("w:color"), "9AA8B7")
        borders.append(border)
    p_pr.append(borders)
    set_run_font(
        paragraph.add_run(f"{label}: "),
        bold=True,
        color=DARK_BLUE,
    )
    paragraph.add_run(text)


def add_cover(doc: Document) -> None:
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(52)

    kicker = doc.add_paragraph()
    kicker.alignment = WD_ALIGN_PARAGRAPH.CENTER
    kicker.paragraph_format.space_after = Pt(18)
    set_run_font(
        kicker.add_run("HUMAN-COMPUTER INTERACTION  |  DA1"),
        size=11,
        color=BLUE,
        bold=True,
    )

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(12)
    set_run_font(
        title.add_run("AI-Based Multimodal Hands-Free\nComputer Interface"),
        size=27,
        color=INK,
        bold=True,
    )

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_after = Pt(26)
    set_run_font(
        subtitle.add_run(
            "Voice and Screen-Target Control with Head/Eye Cursor Movement "
            "and Tongue Gesture Clicking"
        ),
        size=14.5,
        color=DARK_BLUE,
    )

    descriptor = doc.add_paragraph()
    descriptor.alignment = WD_ALIGN_PARAGRAPH.CENTER
    descriptor.paragraph_format.space_after = Pt(34)
    set_run_font(
        descriptor.add_run(
            "Finalized Topic 6 • 30-paper DOI literature review • "
            "Hardware • Software • Methodology"
        ),
        size=10.2,
        color=MUTED,
        italic=True,
    )

    for label, value in [
        ("Submitted by", "________________________________________"),
        ("Roll number", "________________________________________"),
        ("Course / section", "________________________________________"),
        ("Physical presentation deadline", "29.07.2026"),
    ]:
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_after = Pt(7)
        set_run_font(
            paragraph.add_run(f"{label}: "),
            size=11,
            color=INK,
            bold=True,
        )
        set_run_font(paragraph.add_run(value), size=11, color=INK)

    note = doc.add_paragraph()
    note.alignment = WD_ALIGN_PARAGRAPH.CENTER
    note.paragraph_format.space_before = Pt(28)
    set_run_font(
        note.add_run("Final Word report • No PowerPoint required"),
        size=9.5,
        color=MUTED,
    )
    doc.add_page_break()


def add_criteria_table(doc: Document) -> None:
    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    widths = [700, 4300, 850, 3510]
    headers = ["No.", "Assessment requirement", "Marks", "Evidence"]
    for index, value in enumerate(headers):
        table.rows[0].cells[index].text = value
        set_cell_shading(table.rows[0].cells[index], HEADER_FILL)
        set_repeatable_cell_text(
            table.rows[0].cells[index],
            bold=True,
            color=DARK_BLUE,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
    repeat_table_header(table.rows[0])
    rows = [
        ("1", "Review of related literature (at least 25-30 papers)", "4", "Section 3: thematic synthesis plus critical matrix of 30 DOI-linked papers"),
        ("2", "Identifying the required hardware components", "2", "Section 5: required, optional, and explicitly unnecessary hardware"),
        ("3", "Identifying the required software", "2", "Section 6: exact installed stack, models, modules, permissions, and execution"),
        ("4", "Finalizing the methodology", "2", "Section 7: development, evaluation, measures, procedure, analysis, ethics, and criteria"),
    ]
    for values in rows:
        cells = table.add_row().cells
        for index, value in enumerate(values):
            cells[index].text = value
            set_repeatable_cell_text(
                cells[index],
                align=WD_ALIGN_PARAGRAPH.CENTER if index in (0, 2) else WD_ALIGN_PARAGRAPH.LEFT,
            )
    set_table_geometry(table, widths)


def add_contents(doc: Document) -> None:
    doc.add_page_break()
    add_heading(doc, "Contents", 1)
    add_section_intro(
        doc,
        "The report follows the marking scheme and then provides implementation "
        "evidence and appendices for presentation."
    )
    items = [
        "Executive Summary and Assessment Requirements",
        "Topic Finalization — Section 1",
        "Literature Review Method — Section 2",
        "Review of Related Literature (30 Papers) — Section 3",
        "Proposed System and Implemented Architecture — Section 4",
        "Required Hardware Components — Section 5",
        "Required Software — Section 6",
        "Finalized Methodology — Section 7",
        "Implementation Verification, Results, and Limitations — Section 8",
        "Conclusion — Section 9",
        "References (30 DOI Links)",
        "Appendices: Commands, Setup, Test Protocol, and Risk Controls",
    ]
    add_steps(doc, items)
    doc.add_page_break()


def add_literature_matrix(doc: Document) -> None:
    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    widths = [450, 1450, 2100, 5360]
    headers = ["No", "Theme", "Study", "Critical review and project implication"]
    for index, value in enumerate(headers):
        cell = table.rows[0].cells[index]
        cell.text = value
        set_cell_shading(cell, HEADER_FILL)
        set_repeatable_cell_text(
            cell,
            size=8.8,
            bold=True,
            color=DARK_BLUE,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
    repeat_table_header(table.rows[0])
    for index, paper in enumerate(PAPERS, 1):
        cells = table.add_row().cells
        values = [
            str(index),
            paper["theme"],
            f"[{index}] {paper['citation']}",
            paper["review"],
        ]
        for column, value in enumerate(values):
            cells[column].text = value
            set_repeatable_cell_text(
                cells[column],
                size=8.7,
                bold=column == 2,
                color=INK if column == 2 else None,
                align=WD_ALIGN_PARAGRAPH.CENTER if column == 0 else WD_ALIGN_PARAGRAPH.LEFT,
            )
            cells[column].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    set_table_geometry(table, widths)


def add_hardware_table(doc: Document) -> None:
    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    widths = [1600, 1400, 2850, 3510]
    headers = ["Component", "Status", "Development specification", "Purpose / justification"]
    for index, value in enumerate(headers):
        cell = table.rows[0].cells[index]
        cell.text = value
        set_cell_shading(cell, HEADER_FILL)
        set_repeatable_cell_text(
            cell,
            bold=True,
            color=DARK_BLUE,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
    repeat_table_header(table.rows[0])
    rows = [
        ("Laptop", "Required", "Apple M2, 8 GB RAM, arm64", "Runs ASR, camera inference, OCR, GUI, and macOS automation locally."),
        ("Built-in microphone", "Required for voice", "MacBook microphone; mono PCM input", "Captures commands; no external microphone is needed."),
        ("Built-in camera", "Required for camera modes", "FaceTime RGB camera at 640 × 480, approximately 24 fps", "Captures head, iris, and mouth/tongue features."),
        ("Display", "Required", "Integrated MacBook display", "Shows targets, transcript, state, feedback, and evaluation prompts."),
        ("CPU and storage", "Required", "Apple Silicon CPU; storage for cached models and logs", "Runs inference without a dedicated GPU and retains only model/derived CSV files."),
        ("Trackpad or mouse", "Safety fallback", "Existing built-in trackpad or USB/Bluetooth mouse", "Manual recovery, calibration assistance, and PyAutoGUI corner fail-safe."),
        ("Front lighting", "Recommended", "Normal room light or inexpensive desk lamp", "Improves face, iris, and tongue feature stability."),
        ("External microphone", "Optional", "USB or headset microphone", "May improve recognition in high noise; not required for the demonstrated system."),
        ("Laptop stand", "Optional", "Any stable stand", "Reduces camera movement and improves head/gaze calibration."),
        ("Eye tracker / tongue sensor / wearable", "Not required", "None", "The implementation deliberately uses the built-in RGB camera instead."),
        ("Dedicated GPU / robot / VR headset", "Not required", "None", "Outside the finalized topic and unnecessary for this prototype."),
    ]
    for values in rows:
        cells = table.add_row().cells
        for index, value in enumerate(values):
            cells[index].text = value
            set_repeatable_cell_text(
                cells[index],
                size=8.9,
                align=WD_ALIGN_PARAGRAPH.CENTER if index == 1 else WD_ALIGN_PARAGRAPH.LEFT,
            )
    set_table_geometry(table, widths)


def add_software_table(doc: Document) -> None:
    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    widths = [2050, 1450, 2700, 3160]
    headers = ["Software / model", "Installed version", "Role", "Selection rationale"]
    for index, value in enumerate(headers):
        cell = table.rows[0].cells[index]
        cell.text = value
        set_cell_shading(cell, HEADER_FILL)
        set_repeatable_cell_text(
            cell,
            bold=True,
            color=DARK_BLUE,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
    repeat_table_header(table.rows[0])
    rows = [
        ("macOS", "26.5", "Host operating system", "Provides Accessibility, screen capture, window activation, Quartz mouse events, camera, and microphone access."),
        ("Python", "3.12.8", "Main application language", "Readable modular implementation with mature HCI and computer-vision libraries."),
        ("MacParakeet / FluidAudio", "Parakeet TDT 0.6B v3", "Primary offline speech-to-text", "Accurate local recognition using the already installed cached model; no API key or training."),
        ("Swift helper", "Compiled arm64 binary", "Keeps Parakeet warm", "Avoids reloading the model for every command and isolates the native inference process."),
        ("Vosk", "0.3.44", "Offline ASR fallback", "Keeps the application usable if the Parakeet helper cannot start."),
        ("MediaPipe", "0.10.35", "Face and iris landmarks", "Real-time 478-point face tracking from an ordinary RGB camera."),
        ("OpenCV", "5.0.0.93", "Camera capture and frame conversion", "Reliable AVFoundation capture, mirroring, resizing, and RGB conversion."),
        ("NumPy", "2.5.1", "Tongue feature calculations", "Efficient color, saturation, redness, and vector operations."),
        ("PyAutoGUI", "0.9.54", "Cursor movement, scrolling, shortcuts", "Simple automation with an emergency corner fail-safe."),
        ("PyObjC / Quartz / AX", "12.2.1", "Native macOS integration", "Finds controls, activates target applications, and sends genuine multi-click states."),
        ("Tesseract", "5.5.1", "Visible-screen OCR", "Local whole-screen recognition of browser text and desktop folder labels."),
        ("Tkinter", "Python standard library", "Project GUI", "Provides buttons, status, transcript, feedback, evaluation, and logs without a web server."),
        ("unittest", "Python standard library", "Automated verification", "Supports a repeatable 65-test regression suite."),
        ("CSV / threading / subprocess", "Python standard library", "Logging and process isolation", "Keeps outputs readable and prevents audio/camera worker failures from closing the GUI."),
    ]
    for values in rows:
        cells = table.add_row().cells
        for index, value in enumerate(values):
            cells[index].text = value
            set_repeatable_cell_text(
                cells[index],
                size=8.75,
                align=WD_ALIGN_PARAGRAPH.CENTER if index == 1 else WD_ALIGN_PARAGRAPH.LEFT,
            )
    set_table_geometry(table, widths)


def add_verification_table(doc: Document) -> None:
    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    widths = [1800, 3650, 1900, 2010]
    headers = ["Verification layer", "What was verified", "Evidence", "Status"]
    for index, value in enumerate(headers):
        cell = table.rows[0].cells[index]
        cell.text = value
        set_cell_shading(cell, HEADER_FILL)
        set_repeatable_cell_text(
            cell,
            bold=True,
            color=DARK_BLUE,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
    repeat_table_header(table.rows[0])
    rows = [
        ("Automated tests", "Commands, safety states, evaluation, exact word matching, OCR parsing, AX controls, camera/tongue state machine, window activation, and native click states", "65 unit/regression tests", "Passed"),
        ("Dependencies", "Installed Python package consistency", "python -m pip check", "No broken requirements"),
        ("Speech pipeline", "Persistent Parakeet model, Vosk fallback, VAD segmentation, isolated microphone worker", "Live transcription and recovery checks", "Working"),
        ("Camera pipeline", "Head mapping, iris ratios, tongue features, calibration, pointer freeze during gestures", "Unit tests plus live use", "Working"),
        ("Native clicking", "Target app activation, fixed cursor coordinate, Quartz clickState 1/2/3, nonactivating feedback overlay", "Regression tests plus Finder use", "Working"),
        ("Screen targeting", "Exact singular/plural matching, semantic controls first, whole-screen OCR fallback, transcript exclusion", "Unit tests and live use", "Working"),
        ("Guided pilot", "Twelve fixed commands with Parakeet in one development session", "11/12 correct; 91.667%; mean 2.861 s", "Formative only"),
        ("Safety", "Paused and evaluation states never execute actions; destructive actions excluded", "Automated tests and design inspection", "Passed"),
    ]
    for values in rows:
        cells = table.add_row().cells
        for index, value in enumerate(values):
            cells[index].text = value
            set_repeatable_cell_text(
                cells[index],
                size=8.8,
                align=WD_ALIGN_PARAGRAPH.CENTER if index == 3 else WD_ALIGN_PARAGRAPH.LEFT,
            )
    set_table_geometry(table, widths)


def add_references(doc: Document) -> None:
    num_id = create_numbering(doc, fmt="decimal", text="[%1]", left=540, hanging=540)
    for citation, doi in REFERENCES:
        paragraph = doc.add_paragraph()
        apply_numbering(paragraph, num_id)
        paragraph.paragraph_format.left_indent = Inches(0.38)
        paragraph.paragraph_format.first_line_indent = Inches(-0.38)
        paragraph.paragraph_format.space_after = Pt(7)
        paragraph.paragraph_format.line_spacing = 1.15
        paragraph.paragraph_format.keep_together = True
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        set_run_font(paragraph.add_run(citation), size=9.8)
        url = f"https://doi.org/{doi}"
        add_hyperlink(paragraph, f"DOI: {doi}", url)


def keep_table_with_caption(table) -> None:
    for cell in table.rows[-1].cells:
        for paragraph in cell.paragraphs:
            paragraph.paragraph_format.keep_with_next = True


def build_report() -> Path:
    if len(PAPERS) != 30 or len(REFERENCES) != 30:
        raise RuntimeError("The DA1 report must contain exactly 30 reviewed references.")
    create_architecture()
    create_tongue_figure()
    create_methodology_figure()
    create_hardware_figure()

    doc = Document()
    style_document(doc)
    set_header_footer(doc)
    section = doc.sections[0]
    section.header.paragraphs[0].clear()
    set_run_font(
        section.header.paragraphs[0].add_run(
            "HCI DA1  |  Multimodal Hands-Free Computer Interface"
        ),
        size=9,
        color=MUTED,
        bold=True,
    )
    add_cover(doc)

    add_heading(doc, "Executive Summary", 1)
    add_callout(
        doc,
        "Final decision",
        "Submit Proposed Topic 6, “Voice based control of any action,” as an "
        "implemented multimodal assistive HCI project titled “AI-Based Multimodal "
        "Hands-Free Computer Interface: Voice and Screen-Target Control with "
        "Head/Eye Cursor Movement and Tongue Gesture Clicking.”",
    )
    add_text(
        doc,
        "The system is a working macOS prototype rather than a conceptual proposal. "
        "It uses the installed Parakeet TDT 0.6B v3 model for offline speech "
        "recognition, with Vosk as fallback; MediaPipe face landmarks for head, iris, "
        "and mouth analysis; macOS Accessibility and whole-screen OCR for named "
        "targets; PyAutoGUI for movement; and native Quartz events for reliable "
        "single, double, and triple tongue clicks. No custom dataset, cloud API, "
        "wearable sensor, eye tracker, robot, or dedicated GPU is required."
    )
    add_text(
        doc,
        "The literature review contains exactly 30 peer-reviewed works, and every "
        "reference includes a clickable DOI link. The evidence covers voice HCI, "
        "assistive speech recognition, eye-gaze selection, head-operated computer "
        "control, tongue-computer interfaces, and multimodal interaction. The "
        "methodology combines engineering verification with a proposed within-"
        "participant evaluation of effectiveness, efficiency, satisfaction, and safety."
    )
    add_heading(doc, "Assessment Requirements Addressed", 2)
    add_criteria_table(doc)
    add_caption(doc, "Table 1. Direct mapping from DA1 requirements to report evidence.")
    add_contents(doc)

    add_heading(doc, "1. Topic Finalization", 1)
    add_section_intro(
        doc,
        "Primary listed topic: 6. Voice based control of any action "
        "(cursor movement, click of button, and related computer actions)."
    )
    add_heading(doc, "1.1 Final Project Title", 2)
    add_callout(
        doc,
        "Title to submit",
        "AI-Based Multimodal Hands-Free Computer Interface: Voice and Screen-"
        "Target Control with Head/Eye Cursor Movement and Tongue Gesture Clicking.",
    )
    add_text(
        doc,
        "The topic remains anchored to listed Topic 6 because voice commands and "
        "voice-directed action are the main interaction layer. Head/eye movement and "
        "tongue clicking are assistive extensions that strengthen the hands-free "
        "computer-control objective and connect the work to listed Topic 2 without "
        "requiring separate hardware."
    )
    add_heading(doc, "1.2 Problem Statement", 2)
    add_text(
        doc,
        "Conventional mouse and trackpad interaction requires precise, repeated hand "
        "movement. This can be difficult or impossible for people with upper-limb "
        "motor limitations and inconvenient when hands are occupied. Existing "
        "platform accessibility tools may depend on proprietary operating-system "
        "features, specialized sensors, cloud services, or rigid interaction modes. "
        "The problem is to provide a low-cost, locally processed, understandable, and "
        "safe interface that converts speech, head/eye movement, and a deliberate "
        "tongue gesture into normal desktop actions."
    )
    add_heading(doc, "1.3 Aim", 2)
    add_text(
        doc,
        "To design, implement, and evaluate an AI-based multimodal hands-free "
        "interface that enables cursor movement, clicking, screen-target activation, "
        "scrolling, and basic shortcuts using only a MacBook microphone and camera."
    )
    add_heading(doc, "1.4 Objectives", 2)
    add_bullets(
        doc,
        [
            "Recognize a small, discoverable command vocabulary using an offline pretrained speech model.",
            "Move the pointer continuously from calibrated head motion or estimated eye gaze.",
            "Recognize complete tongue-out-and-retract gestures and generate reliable single, double, and triple clicks.",
            "Locate spoken buttons and visible words using macOS Accessibility first and screen OCR second.",
            "Prevent the transcript or text-entry fields from becoming accidental click targets.",
            "Keep control local, reversible, observable, and disabled whenever the system is paused or evaluated.",
            "Measure effectiveness, efficiency, satisfaction, errors, and safety using a reproducible methodology.",
        ],
    )
    add_heading(doc, "1.5 Research Questions", 2)
    add_bullets(
        doc,
        [
            "RQ1: How accurately and quickly does the offline recognizer map spoken commands to the intended computer action?",
            "RQ2: How effectively can users acquire screen targets using calibrated head or eye-gaze pointer movement?",
            "RQ3: How reliably do one, two, and three complete tongue gestures produce their intended click counts without repeats from holding?",
            "RQ4: Does multimodal control improve task completion compared with relying on voice-only discrete movement?",
            "RQ5: What recognition, calibration, lighting, noise, focus, and fatigue conditions produce the most important usability failures?",
        ],
    )
    add_heading(doc, "1.6 Scope and Boundaries", 2)
    add_bullets(
        doc,
        [
            "In scope: cursor movement, left/double/triple/right click, scrolling, tabs, browser opening, named visible targets, feedback, logging, and evaluation.",
            "Out of scope: conversational assistance, unrestricted natural-language automation, destructive actions, purchases, messaging, authentication, medical diagnosis, and clinical claims.",
            "The standard RGB camera provides approximate gaze direction, not clinical eye tracking.",
            "The project uses its own camera and tongue-recognition code; Apple Head Pointer and Alternate Pointer Actions are not used.",
        ],
    )

    doc.add_page_break()
    add_heading(doc, "2. Literature Review Method", 1)
    add_heading(doc, "2.1 Review Type and Sources", 2)
    add_text(
        doc,
        "This is a focused critical review supporting topic finalization, not a claim "
        "of a new systematic review. Searches covered Crossref/DOI metadata and "
        "peer-reviewed works from ACM, IEEE, Oxford University Press, Elsevier, "
        "Springer, Taylor & Francis, Cambridge University Press, MDPI, PNAS, and the "
        "Journal of Rehabilitation Research and Development. Foundational studies "
        "were retained because they define recurring HCI problems such as Midas touch, "
        "dwell selection, multimodal correction, head-control gain, and tongue input."
    )
    add_heading(doc, "2.2 Search Concepts", 2)
    add_bullets(
        doc,
        [
            "voice user interface AND usability AND accessibility",
            "speech cursor control OR vocal joystick OR hands-free computer access",
            "eye gaze interaction OR gaze pointing OR eye typing",
            "head-operated computer control OR camera mouse OR face tracking mouse",
            "tongue-computer interface OR tongue drive assistive technology",
            "multimodal interaction AND motor disability AND error correction",
        ],
    )
    add_heading(doc, "2.3 Inclusion and Exclusion Criteria", 2)
    add_bullets(
        doc,
        [
            "Included: peer-reviewed journal or conference papers directly relevant to at least one implemented interaction channel, usability, accessibility, or evaluation.",
            "Included: systematic/scoping reviews and foundational empirical work needed to explain design choices.",
            "Included only when a resolvable DOI was available; all 30 DOI links are provided in References.",
            "Excluded: product marketing pages, non-scholarly tutorials, papers without DOI identifiers, unrelated speech applications, and hardware-only work with no HCI implication.",
            "Final evidence set: 30 papers published between 1991 and 2024.",
        ],
    )
    add_heading(doc, "2.4 Evidence Organization", 2)
    add_text(
        doc,
        "The 30 papers are synthesized into six connected themes: speech-interface "
        "design and evaluation; assistive voice access; gaze interaction; camera/head "
        "control; tongue interaction; and multimodal integration. Each matrix entry "
        "states both the contribution and its implication for this implementation."
    )

    doc.add_page_break()
    add_heading(doc, "3. Review of Related Literature", 1)
    add_section_intro(
        doc,
        "The literature supports the project's feasibility while warning that accuracy, "
        "intent, calibration, fairness, fatigue, and recovery must be evaluated together."
    )
    add_heading(doc, "3.1 Speech HCI, Usability, and Accessibility", 2)
    add_text(
        doc,
        "Broad reviews demonstrate a large and mature evidence base. Clark et al. [1] "
        "map speech HCI themes including accessibility and evaluation, while Deshmukh "
        "and Chalmeta [2] identify persistent weaknesses in error recovery, inclusion, "
        "and standardized measures. Dutsinma et al. [3] reinforce the ISO 9241-11 "
        "dimensions of effectiveness, efficiency, and satisfaction. The Vocal "
        "Joystick studies [4], [5] establish voice-driven pointing as feasible and "
        "learnable, whereas EMKEY [6] demonstrates low-cost multimodal computer control."
    )
    add_text(
        doc,
        "Speech is not automatically accessible. Work on dexterity-limited users [7], "
        "mouse-versus-speech choice [8], dysarthric speech [9], disability contexts "
        "[10], and ALS [11] shows that users, speech characteristics, and tasks matter. "
        "SASSI [12] supplies validated subjective constructs. Expectation, privacy, and "
        "fairness findings [13]-[15] motivate a transparent command-based design, local "
        "processing, diverse testing, and cautious claims. Multimodal error correction "
        "[16] supports retaining alternative input paths."
    )
    add_heading(doc, "3.2 Eye-Gaze Interaction", 2)
    add_text(
        doc,
        "Jacob [17] frames the central gaze-interface problem: people look naturally, "
        "but the system must not interpret every look as a command. Sibert and Jacob "
        "[18] demonstrate gaze-selection potential, while MAGIC pointing [19] combines "
        "gaze with another modality so gaze assists rather than solely decides. Eye-"
        "typing experience [20] emphasizes dwell, calibration, feedback, and Midas "
        "touch. Fitts-law comparison [21] provides a principled way to evaluate target "
        "acquisition. The project's separate tongue click is therefore a deliberate "
        "solution to gaze intention ambiguity."
    )
    add_heading(doc, "3.3 Head and Face Tracking", 2)
    add_text(
        doc,
        "Camera Mouse [22] provides the strongest precedent for webcam-only access. "
        "Head-control comparisons [23] and adaptive control [24] show that mapping, "
        "gain, and user-specific configuration affect performance. Face-as-mouse work "
        "[25] supplies a visual-tracking precedent, while OpenFace 2.0 [26] represents "
        "modern facial landmark, head-pose, and gaze analysis. These findings motivate "
        "neutral-position calibration, smoothing, dead zones, adjustable motion gain, "
        "and a stop/recalibrate control."
    )
    add_heading(doc, "3.4 Tongue-Based Interaction", 2)
    add_text(
        doc,
        "Tongue Drive research establishes the tongue as a viable intentional channel "
        "for severe motor impairment [27]-[29]. However, those systems use magnetic or "
        "intraoral sensing. This project studies a different engineering trade-off: "
        "non-contact webcam classification using mouth landmarks and color/geometry "
        "features. It is cheaper and less intrusive, but more sensitive to lighting, "
        "pose, occlusion, and calibration. The literature justifies the modality, not "
        "equivalence between webcam recognition and a clinical-grade sensor."
    )
    add_heading(doc, "3.5 Multimodal Integration and Design Implications", 2)
    add_text(
        doc,
        "Oviatt et al. [30] show that users become more multimodal as task demands "
        "increase. The final design therefore assigns complementary roles instead of "
        "duplicating everything: speech invokes named or discrete actions; head or eye "
        "movement supplies continuous direction; tongue gestures confirm selection; "
        "Accessibility/OCR supplies target awareness; and manual input remains a "
        "fallback. This division also improves recovery when one channel fails."
    )
    add_heading(doc, "3.6 Critical Review Matrix: 30 Papers", 2)
    add_literature_matrix(doc)
    add_caption(doc, "Table 2. Critical review and design implication of all 30 DOI-linked papers.")
    add_heading(doc, "3.7 Identified Research Gap", 2)
    add_callout(
        doc,
        "Gap",
        "Prior work separately establishes voice control, gaze pointing, webcam head "
        "tracking, and sensor-based tongue input. A useful student HCI contribution is "
        "to integrate these findings into one software-only laptop prototype with "
        "offline recognition, visible-screen targeting, calibrated tongue click counts, "
        "native macOS focus/click behavior, safety states, and reproducible evaluation.",
    )
    add_heading(doc, "3.8 Design Requirements Derived from Literature", 2)
    add_bullets(
        doc,
        [
            "Use local pretrained models and a visible fixed command vocabulary.",
            "Separate pointer movement from intentional selection to reduce Midas-touch errors.",
            "Calibrate head, gaze, and tongue features per user; provide quick recalibration.",
            "Expose recognized text, active mode, target selection, and action outcome.",
            "Support multimodal recovery and preserve the physical mouse/trackpad.",
            "Evaluate effectiveness, efficiency, satisfaction, fairness, fatigue, and safety.",
            "Avoid universal-accessibility claims until tested with representative target users.",
        ],
    )

    doc.add_page_break()
    add_heading(doc, "4. Proposed System and Implemented Architecture", 1)
    add_heading(doc, "4.1 Functional Capabilities", 2)
    add_bullets(
        doc,
        [
            "Voice commands: movement, click, double click, right click, scrolling, browser opening, tab actions, pause, and resume.",
            "Voice-directed screen actions: click, double click, right click, or move to an exact visible word/control.",
            "Head tracking: relative joystick-like pointer movement after neutral-position calibration.",
            "Eye-gaze mode: relative pointer motion estimated from both irises within eye bounds.",
            "Tongue control: calibrated complete gestures mapped to single, double, and triple native clicks.",
            "Feedback: transcript, recognizer/mode status, action result, tongue status, and numbered click rings.",
            "Evaluation: randomized prompts, timeouts, correctness, response time, and CSV export.",
        ],
    )
    add_heading(doc, "4.2 Complete System Architecture", 2)
    add_figure(
        doc,
        ARCHITECTURE_PATH,
        "Figure 1. Implemented multimodal processing and control architecture.",
        "Four local input paths—voice, camera movement, tongue gestures, and screen-target search—converge on a safety and action executor.",
    )
    add_text(
        doc,
        "The architecture deliberately isolates failure-prone native resources. "
        "Microphone capture and camera inference run in worker processes so a CoreAudio "
        "or camera failure does not close the interface. The warm Swift Parakeet helper "
        "avoids model reload on each utterance. All OS actions pass through an enabled/"
        "paused gate and macOS permission checks."
    )
    add_heading(doc, "4.3 Voice and Visible-Target Pipeline", 2)
    add_steps(
        doc,
        [
            "Capture microphone PCM in an isolated worker and estimate the local background-noise floor.",
            "Segment one utterance using adaptive energy, pre-roll, silence, minimum, and maximum duration thresholds.",
            "Transcribe locally with the persistent MacParakeet model; fall back to Vosk if the helper is unavailable.",
            "Normalize case and punctuation and match only supported commands or exact aliases.",
            "For a named target, inspect genuine AX buttons, links, menu items, icons, and controls across visible applications.",
            "If semantic control search fails, capture the visible main screen and run local Tesseract OCR.",
            "Exclude the entire Voice Cursor transcript/text region and require word-sensitive exact matching.",
            "Activate the application beneath the selected point, perform the action, display feedback, and append a CSV log row.",
        ],
    )
    add_heading(doc, "4.4 Head and Eye-Gaze Pointer Mapping", 2)
    add_text(
        doc,
        "The camera worker mirrors 640 × 480 frames and runs MediaPipe Face Landmarker "
        "at approximately 24 fps. Head control averages face center and nose position. "
        "Eye-gaze control computes each iris position relative to its eye corners and "
        "lids, then averages both eyes. A short center-looking calibration estimates "
        "neutral position; a dead zone suppresses jitter; nonlinear gain turns larger "
        "displacement into faster relative movement; and smoothing prevents abrupt jumps."
    )
    add_heading(doc, "4.5 Tongue Detection and Clicking", 2)
    add_figure(
        doc,
        TONGUE_PATH,
        "Figure 2. User-calibrated tongue gesture aggregation and click generation.",
        "Neutral and tongue profiles feed a gesture state machine; one, two, or three complete gestures generate corresponding native clicks.",
    )
    add_text(
        doc,
        "Calibration records 28 closed-mouth feature vectors and 28 tongue-out vectors. "
        "Each vector combines redness, upper-quantile redness, pink-pixel fraction, "
        "saturation, and normalized mouth opening. Projection between the two median "
        "profiles produces a likelihood. Separate present/absent thresholds, consecutive-"
        "frame confirmation, minimum duration, cooldown, and full retraction prevent a "
        "held tongue from producing repeated clicks."
    )
    add_text(
        doc,
        "The pointer freezes as soon as a possible gesture begins and remains fixed "
        "through the 0.7-second aggregation window. Double and triple clicks use Quartz "
        "mouse events whose clickState fields are explicitly 1-2 or 1-2-3. This is "
        "necessary for Finder to open folders/documents reliably. The visual click ring "
        "is a nonactivating, click-through panel and cannot steal focus."
    )
    add_heading(doc, "4.6 Safety, Privacy, and Failure Handling", 2)
    add_bullets(
        doc,
        [
            "Pause immediately disables voice actions and stops camera movement.",
            "Guided evaluation recognizes commands but deliberately performs no OS action.",
            "PyAutoGUI's corner fail-safe remains active.",
            "Application activation occurs before clicking so the target—not Voice Cursor—becomes frontmost.",
            "Static text, transcript text, and text fields are excluded from semantic clicking.",
            "No destructive commands are supported.",
            "Raw audio, screenshots, camera frames, and face landmarks are not retained.",
            "Parakeet, Vosk, MediaPipe, and Tesseract processing remain local after model installation.",
        ],
    )

    add_heading(doc, "5. Required Hardware Components", 1)
    add_section_intro(
        doc,
        "The complete prototype requires only one ordinary MacBook; all specialized "
        "assistive sensors are optional or unnecessary."
    )
    add_figure(
        doc,
        HARDWARE_PATH,
        "Figure 3. Minimal one-device hardware configuration.",
        "A MacBook supplies the camera, microphone, display, processor, storage, and safety trackpad; no specialized sensors are required.",
    )
    add_hardware_table(doc)
    add_caption(doc, "Table 3. Required, recommended, optional, and unnecessary hardware.")
    add_heading(doc, "5.1 Hardware Cost and Feasibility", 2)
    add_text(
        doc,
        "Incremental project hardware cost is effectively zero when a MacBook is "
        "already available. Normal room lighting is sufficient in most conditions. "
        "An external microphone or lamp may improve robustness but is not required. "
        "This cost profile is a major advantage over infrared eye trackers, magnetic "
        "tongue systems, wearable bend sensors, VR headsets, robots, and EEG equipment."
    )

    doc.add_page_break()
    add_heading(doc, "6. Required Software", 1)
    add_software_table(doc)
    add_caption(doc, "Table 4. Exact software and model stack used by the implemented prototype.")
    add_heading(doc, "6.1 Project Module Structure", 2)
    add_bullets(
        doc,
        [
            "voice_cursor/app.py — Tk GUI, callbacks, state display, logs, and guided evaluation.",
            "voice_cursor/parakeet_speech.py — VAD, persistent Parakeet helper, and isolated microphone capture.",
            "voice_cursor/speech.py — Vosk fallback, device selection, and model handling.",
            "voice_cursor/commands.py — fixed commands, exact aliases, and visible-target action parsing.",
            "voice_cursor/accessibility_controls.py — semantic macOS AX control discovery with text-field exclusion.",
            "voice_cursor/screen_text.py — screen capture, Tesseract OCR, exact matching, and exclusion rectangles.",
            "voice_cursor/camera_worker.py — MediaPipe face/iris landmarks and tongue feature extraction.",
            "voice_cursor/camera_control.py — head/gaze mapping, calibration, tongue state machine, and click dispatch.",
            "voice_cursor/window_activation.py — frontmost application detection and activation beneath the cursor.",
            "voice_cursor/macos_clicks.py — native fixed-coordinate single/double/triple click-state events.",
            "voice_cursor/click_overlay_worker.py — nonactivating numbered click-ring animation.",
            "tests/ — 65 automated tests covering all safety-critical pure logic and integrations.",
        ],
    )
    add_heading(doc, "6.2 Required macOS Permissions", 2)
    add_bullets(
        doc,
        [
            "Microphone — spoken command capture.",
            "Camera — head, iris, and tongue feature capture.",
            "Accessibility — cursor control and semantic AX actions.",
            "Screen & System Audio Recording — visible-screen capture for OCR.",
            "Permissions must be granted to the application used to launch the project, normally Terminal, followed by an application restart.",
        ],
    )
    add_heading(doc, "6.3 Installation and Execution", 2)
    add_steps(
        doc,
        [
            "Open Terminal and change directory to /Users/utkarshkhajuria/Desktop/HCI PROJECT.",
            "Create/activate the .venv environment and install the package dependencies.",
            "Install Tesseract 5 using Homebrew if visible-screen text targeting is required.",
            "Run the application first in dry-run mode to verify microphone transcription without OS actions.",
            "Grant the four macOS permissions and restart the application.",
            "Launch live mode with ./run_live.command and wait for “Listening with MacParakeet.”",
            "Start Head Tracking or Eye Gaze, calibrate at screen center, then calibrate Tongue Clicks.",
        ],
    )

    add_heading(doc, "7. Finalized Methodology", 1)
    add_figure(
        doc,
        METHODOLOGY_PATH,
        "Figure 4. Finalized evidence-to-evaluation methodology.",
        "Six-stage methodology from literature and implementation through verification, pilot testing, measurement, and analysis.",
    )
    add_heading(doc, "7.1 Development Method", 2)
    add_steps(
        doc,
        [
            "Translate the literature into requirements for privacy, discoverability, calibration, multimodality, feedback, safety, and measurable outcomes.",
            "Implement offline speech recognition and exact command parsing before enabling any live OS action.",
            "Implement semantic target discovery, screen OCR fallback, and strict exclusion of transcripts/text fields.",
            "Implement head and gaze relative mapping with neutral calibration, smoothing, dead zones, and nonlinear speed.",
            "Implement user-specific tongue feature calibration and a complete out/retract gesture state machine.",
            "Use native macOS activation and click-state events so background applications and Finder receive normal clicks.",
            "Isolate microphone, model, camera, and feedback workers to prevent native failures from terminating the GUI.",
            "Verify pure logic and integration paths with automated tests before human trials.",
        ],
    )
    add_heading(doc, "7.2 Study Design", 2)
    add_text(
        doc,
        "Use a within-participant formative study with 12 adult volunteers. Each "
        "participant completes the same tasks under two acoustic conditions (quiet and "
        "moderate recorded background noise) and two movement modes (head and gaze). "
        "Condition order is counterbalanced to reduce learning effects. Tongue click "
        "tasks occur in both movement modes. Voice-only discrete movement is included "
        "as a baseline for one target-acquisition block."
    )
    add_heading(doc, "7.3 Participants", 2)
    add_bullets(
        doc,
        [
            "Target: 12 adults for a classroom formative study; record age band, prior voice-assistant use, corrective lenses, and main spoken languages only with consent.",
            "Seek variation in accents and computer experience because ASR fairness literature makes homogenous sampling a validity risk.",
            "Do not claim clinical accessibility from non-disabled participants.",
            "Testing people with motor disabilities requires accessible consent, ethics approval, appropriate recruitment, and a separate risk review.",
        ],
    )
    add_heading(doc, "7.4 Apparatus and Controlled Conditions", 2)
    add_bullets(
        doc,
        [
            "Same Apple M2 MacBook, display resolution, built-in camera, microphone, chair distance, and interface version for all trials.",
            "Camera approximately at eye level, participant 50-70 cm from the display, with even front lighting.",
            "Quiet condition documented using ambient sound-level measurement; noise condition uses the same speaker, file, volume, and position.",
            "Pointer begins from a fixed center location; target sizes and distances are logged.",
            "Actions remain non-destructive and a facilitator keeps the physical trackpad available for immediate recovery.",
        ],
    )
    add_heading(doc, "7.5 Tasks", 2)
    add_steps(
        doc,
        [
            "Complete a two-minute voice-command practice in dry-run mode.",
            "Complete center-looking head calibration followed by large and small target-acquisition trials.",
            "Complete eye-gaze calibration followed by the same randomized target set.",
            "Complete closed-mouth and tongue-out calibration.",
            "Select a file once, open a Finder folder with two tongue gestures, and generate a triple click with three gestures.",
            "Use voice to click named AX controls and visible OCR text, including exact singular/plural tests.",
            "Complete twelve randomized guided voice-command trials in quiet and noise.",
            "Pause control and verify that voice/camera inputs produce zero OS actions.",
        ],
    )
    add_heading(doc, "7.6 Variables and Operational Measures", 2)
    add_bullets(
        doc,
        [
            "Independent variables: movement mode (head, gaze, voice baseline), acoustic condition (quiet, moderate noise), target size/distance, and click count.",
            "Voice accuracy (%) = correctly mapped command trials ÷ total prompted trials × 100.",
            "Target completion (%) = successfully selected/opened targets ÷ attempted targets × 100.",
            "Movement time = target appearance to pointer entry; selection time = target appearance to completed click.",
            "Click-count accuracy (%) = gestures producing intended single/double/triple action ÷ click trials × 100.",
            "Error categories: unrecognized, substitution, wrong target, false activation, missed gesture, repeated click, focus error, timeout, and calibration loss.",
            "Subjective measures: seven-point SASSI-aligned ratings for response accuracy, speed, cognitive demand, annoyance, likeability, and habitability.",
            "Safety measure: unintended actions while paused/evaluating; acceptance requirement is zero.",
        ],
    )
    add_heading(doc, "7.7 Procedure", 2)
    add_steps(
        doc,
        [
            "Explain the study, privacy boundary, non-medical status, pause command, and withdrawal right; obtain informed consent.",
            "Record minimal participant background data without names in analysis files.",
            "Adjust seating and lighting, then demonstrate every mode without collecting scored data.",
            "Run the counterbalanced movement-mode blocks with a short rest between them.",
            "Run the randomized quiet and noise voice blocks using guided evaluation.",
            "Export CSV results and record calibration/restart events on the observation sheet.",
            "Administer the SASSI-aligned questionnaire and one open-ended improvement question.",
            "Debrief, remove direct identifiers, and delete any incidental recordings; the application itself stores no raw audio/video.",
        ],
    )
    add_heading(doc, "7.8 Analysis Plan", 2)
    add_text(
        doc,
        "Report participant-level and condition-level median, mean, standard "
        "deviation, interquartile range, minimum, and maximum. Plot command confusion "
        "counts and target-completion errors. Compare paired quiet/noise accuracy and "
        "response time, and paired head/gaze completion time, using Wilcoxon signed-rank "
        "tests because the formative sample is small and normality should not be "
        "assumed. Report effect sizes and individual distributions rather than relying "
        "only on p-values. Analyze comments thematically for calibration, fatigue, "
        "discoverability, confidence, and privacy."
    )
    add_heading(doc, "7.9 Acceptance Criteria", 2)
    add_bullets(
        doc,
        [
            "Voice command accuracy of at least 85% in quiet conditions.",
            "Median final voice-command response time no greater than 3 seconds.",
            "At least 80% target completion for head and gaze blocks after practice.",
            "At least 90% intended click-count accuracy after tongue calibration.",
            "Zero executed actions during paused and guided-evaluation states.",
            "No application crash during a complete participant session.",
        ],
    )
    add_heading(doc, "7.10 Ethics, Privacy, and Risk Control", 2)
    add_bullets(
        doc,
        [
            "Obtain informed consent and permit withdrawal without penalty.",
            "Do not retain raw voice, camera frames, face landmarks, or screenshots.",
            "Use anonymous participant codes and encrypted storage for derived CSV data.",
            "Offer rest breaks because sustained head, eye, or tongue movement may cause fatigue.",
            "Stop immediately for pain, dizziness, eye strain, jaw discomfort, or loss of control.",
            "Exclude destructive and security-sensitive actions and keep the trackpad available.",
            "Report failures and demographic limitations; do not market the prototype as certified assistive technology.",
        ],
    )

    doc.add_page_break()
    add_heading(doc, "8. Implementation Verification, Results, and Limitations", 1)
    add_heading(doc, "8.1 Completed Verification", 2)
    add_verification_table(doc)
    add_caption(doc, "Table 5. Current engineering and formative verification evidence.")
    add_callout(
        doc,
        "Correct interpretation",
        "The 65 passing tests establish regression coverage for implemented logic. "
        "The 11/12 guided result shows that one development session can achieve "
        "91.667% command accuracy with a 2.861-second mean response. Neither result "
        "proves general usability, fairness, clinical accessibility, or performance "
        "under controlled noise; those claims require the Section 7 study.",
    )
    add_heading(doc, "8.2 Strengths", 2)
    add_bullets(
        doc,
        [
            "One-device, zero-specialized-hardware architecture.",
            "Offline-first speech and computer vision with no subscription or API key.",
            "Complementary modalities rather than dependence on one recognition channel.",
            "Exact visible-target matching and explicit exclusion of transcript/text-entry regions.",
            "Reliable macOS focus behavior and genuine native double/triple click states.",
            "User-specific calibration, reversible controls, visual feedback, and process isolation.",
            "Reproducible logs, guided evaluation, and extensive automated tests.",
        ],
    )
    add_heading(doc, "8.3 Limitations", 2)
    add_bullets(
        doc,
        [
            "Webcam gaze estimation is approximate and more sensitive than dedicated infrared eye tracking.",
            "Tongue color/geometry varies with lighting, complexion, camera exposure, pose, occlusion, and individual anatomy.",
            "Head and gaze movement may fatigue users and currently use a fixed gain configuration.",
            "Parakeet/Vosk performance may differ across accents, speech impairments, noise, and microphone placement.",
            "OCR sees only visible pixels; minimized or fully covered windows cannot be targeted.",
            "The implementation is macOS-specific in its accessibility, screen, focus, and native click integrations.",
            "No controlled study with target users has yet been completed.",
        ],
    )
    add_heading(doc, "8.4 Future Work", 2)
    add_bullets(
        doc,
        [
            "Add a graphical sensitivity/calibration wizard and store opt-in per-user profiles locally.",
            "Fuse head and gaze estimates adaptively and add dwell as an optional alternative click.",
            "Improve tongue features with illumination normalization and temporal classification.",
            "Add multilingual/local speech models and consented adaptation for Indian English.",
            "Evaluate target users with appropriate ethics and accessible study procedures.",
            "Package the application as a signed macOS app so permissions attach to one stable application identity.",
        ],
    )

    add_heading(doc, "9. Conclusion", 1)
    add_text(
        doc,
        "The finalized project is technically feasible, academically defensible, and "
        "already implemented. It remains grounded in Proposed Topic 6 while adding "
        "camera-based assistive modalities that make hands-free control more continuous "
        "and practical. Thirty DOI-linked papers establish the scientific context and "
        "expose the central HCI risks. Required hardware and software are fully "
        "identified, and the finalized methodology specifies participants, conditions, "
        "tasks, variables, measures, analysis, ethics, and acceptance criteria. The "
        "report therefore addresses all four DA1 marking components and provides clear "
        "evidence for physical presentation."
    )

    add_heading(doc, "References", 1)
    add_section_intro(
        doc,
        "Exactly 30 scholarly references are listed below. Every entry includes the "
        "mandatory clickable DOI link."
    )
    add_references(doc)

    doc.add_page_break()
    add_heading(doc, "Appendix A. Supported Voice Commands", 1)
    add_bullets(
        doc,
        [
            "Movement: move left, move right, move up, move down.",
            "Pointer actions: click, double click, right click.",
            "Screen targets: click <words>, double click <words>, right click <words>, move to <words>.",
            "Scrolling: scroll up, scroll down.",
            "Browser/keyboard: open browser, new tab, close tab.",
            "Safety state: pause control, resume control.",
            "Matching rule: case and punctuation are normalized, but singular/plural spellings remain distinct.",
        ],
    )
    add_heading(doc, "Appendix B. Physical Presentation Checklist", 1)
    add_bullets(
        doc,
        [
            "Connect power and close applications that may use the camera or microphone.",
            "Verify Microphone, Camera, Accessibility, and Screen Recording permissions for Terminal.",
            "Launch ./run_live.command and wait for “Listening with MacParakeet.”",
            "Demonstrate one voice movement and one named screen-target click.",
            "Start Head Tracking, look at center during calibration, then move the pointer.",
            "Calibrate Tongue Clicks and demonstrate single click followed by a true Finder double click.",
            "Show the numbered click ring, pause control, and verify that movement/actions stop.",
            "Keep a physical mouse/trackpad available and avoid destructive targets during presentation.",
        ],
    )
    add_heading(doc, "Appendix C. Evaluation Data Fields", 1)
    add_bullets(
        doc,
        [
            "participant_code, condition_order, movement_mode, acoustic_condition",
            "target_id, target_size, target_distance, expected_command/click_count",
            "recognized_text, matched_command, target_completed, response_time_seconds",
            "error_category, calibration_repeated, unintended_action, observer_note",
            "SASSI-aligned item ratings and one open-ended comment",
        ],
    )
    doc.add_page_break()
    add_heading(doc, "Appendix D. Traceability Matrix", 1)
    trace = doc.add_table(rows=1, cols=3)
    trace.style = "Table Grid"
    widths = [2400, 3400, 3560]
    for index, value in enumerate(["Literature finding", "Implemented response", "Planned measure"]):
        trace.rows[0].cells[index].text = value
        set_cell_shading(trace.rows[0].cells[index], ACCENT_FILL)
        set_repeatable_cell_text(
            trace.rows[0].cells[index],
            bold=True,
            color=DARK_BLUE,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
    repeat_table_header(trace.rows[0])
    trace_rows = [
        ("Speech errors and expectation gaps [1]-[3], [13]", "Fixed commands, live transcript, exact matching, visible feedback", "Accuracy, error category, SASSI accuracy/habitability"),
        ("ASR disparities and disability variability [9]-[11], [15]", "Offline model with explicit limitations and fallback", "Accent/language context and participant-level results"),
        ("Midas touch and gaze calibration [17]-[21]", "Gaze moves pointer; tongue confirms click; recalibration and dead zone", "Target completion, movement/selection time, false activations"),
        ("Head-control adaptation [22]-[26]", "Neutral calibration, smoothing, nonlinear gain, stop control", "Head/gaze comparison, fatigue, calibration repeats"),
        ("Tongue intention [27]-[29]", "User-specific profiles, out/retract confirmation, fixed-position native clicks", "Single/double/triple click-count accuracy"),
        ("Multimodal use and recovery [16], [30]", "Voice, camera, tongue, GUI, and manual fallback coexist", "Task completion by mode and qualitative preference"),
    ]
    for values in trace_rows:
        cells = trace.add_row().cells
        for index, value in enumerate(values):
            cells[index].text = value
            set_repeatable_cell_text(cells[index], size=8.9)
    set_table_geometry(trace, widths)
    add_caption(doc, "Table 6. Literature-to-design-to-measure traceability.")

    doc.save(OUTPUT_PATH)
    return OUTPUT_PATH


if __name__ == "__main__":
    print(build_report())

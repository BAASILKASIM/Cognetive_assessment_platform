import random

ICON_BANK = [
    {"id": "car-front-fill", "label": "Car"},
    {"id": "book-fill", "label": "Book"},
    {"id": "camera-fill", "label": "Camera"},
    {"id": "key-fill", "label": "Key"},
    {"id": "watch", "label": "Watch"},
    {"id": "music-note-beamed", "label": "Music"},
    {"id": "tree-fill", "label": "Tree"},
    {"id": "heart-fill", "label": "Heart"},
    {"id": "house-door-fill", "label": "House"},
    {"id": "bicycle", "label": "Bicycle"},
    {"id": "airplane-fill", "label": "Airplane"},
    {"id": "alarm-fill", "label": "Alarm Clock"},
    {"id": "apple", "label": "Apple"},
    {"id": "bag-fill", "label": "Bag"},
    {"id": "balloon-fill", "label": "Balloon"},
    {"id": "bell-fill", "label": "Bell"},
    {"id": "binoculars-fill", "label": "Binoculars"},
    {"id": "brightness-high-fill", "label": "Sun"},
    {"id": "bucket-fill", "label": "Bucket"},
    {"id": "bug-fill", "label": "Bug"},
    {"id": "cup-hot-fill", "label": "Coffee Cup"},
    {"id": "egg-fill", "label": "Egg"},
    {"id": "emoji-smile-fill", "label": "Smile"},
    {"id": "gift-fill", "label": "Gift"},
    {"id": "globe-americas", "label": "Globe"},
    {"id": "hammer", "label": "Hammer"},
    {"id": "headphones", "label": "Headphones"},
    {"id": "lightbulb-fill", "label": "Light Bulb"},
    {"id": "lock-fill", "label": "Lock"},
    {"id": "moon-stars-fill", "label": "Moon"},
]


def generate_recognition_data():
    """Generates 8 random study icons and 5 dynamic questions."""
    study_icons = random.sample(ICON_BANK, 8)
    study_ids = {icon["id"] for icon in study_icons}
    non_study_icons = [icon for icon in ICON_BANK if icon["id"] not in study_ids]

    questions = []
    targets = random.sample(study_icons, 5)

    question_prompts = [
        "Which of these objects was presented in the memorization screen?",
        "Which item did you study in the original set of 8 objects?",
        "Identify the object that appeared in the 10-second exposure window:",
        "Select the item from the memorized list:",
        "Which of the following objects was in the 8-item exposure set?",
    ]

    for i in range(5):
        target = targets[i]
        distractors = random.sample(non_study_icons, 3)
        options = [target] + distractors
        random.shuffle(options)
        questions.append({
            "question": question_prompts[i],
            "options": options,
            "answer": target["label"],
        })

    return study_icons, questions


def generate_object_location_data():
    """Generates 3 rounds of random icons placed in random 3x3 grid positions (0..8).
    Ensures icons and tile positions are unique across rounds (no repeated icons or identical tile layouts).
    """
    counts = [3, 4, 5]
    total_icons_needed = sum(counts)  # 12 unique icons across 3 rounds

    # Pick 12 unique icons from ICON_BANK for the entire game session (no repeats across rounds)
    selected_icons = random.sample(ICON_BANK, total_icons_needed)

    game_data = []
    icon_idx = 0
    previous_position_sets = []

    for count in counts:
        round_icons = selected_icons[icon_idx : icon_idx + count]
        icon_idx += count

        # Sample tile positions (0..8) ensuring variance across rounds
        positions = random.sample(range(9), count)
        attempts = 0
        while set(positions) in previous_position_sets and attempts < 10:
            positions = random.sample(range(9), count)
            attempts += 1

        previous_position_sets.append(set(positions))

        round_items = []
        for icon, pos in zip(round_icons, positions):
            round_items.append({
                "icon": icon,
                "position": pos
            })
        game_data.append(round_items)

    return game_data



def generate_delayed_recall_data(study_icons=None, location_game_data=None):
    """Generates 4 dynamic delayed recall questions based on session study icons and location data."""
    if not study_icons:
        study_icons = random.sample(ICON_BANK, 8)

    study_ids = {icon["id"] for icon in study_icons}
    non_study_icons = [icon for icon in ICON_BANK if icon["id"] not in study_ids]

    loc_icons = []
    if location_game_data:
        for r in location_game_data:
            for item in r:
                loc_icons.append(item["icon"])
    if not loc_icons:
        loc_icons = random.sample(ICON_BANK, 5)

    loc_ids = {icon["id"] for icon in loc_icons}
    non_loc_icons = [icon for icon in ICON_BANK if icon["id"] not in loc_ids]

    questions = []

    # Q1: Recognition Recall
    target1 = random.choice(study_icons)
    distractors1 = random.sample(non_study_icons, 3)
    opts1 = [target1] + distractors1
    random.shuffle(opts1)
    questions.append({
        "question": "Which object was part of the original 8-item recognition exposure set?",
        "options": opts1,
        "answer": target1["label"]
    })

    # Q2: Spatial Location Recall
    target2 = random.choice(loc_icons)
    distractors2 = random.sample(non_loc_icons, 3)
    opts2 = [target2] + distractors2
    random.shuffle(opts2)
    questions.append({
        "question": "Which item was placed on the 3×3 grid during the spatial location test?",
        "options": opts2,
        "answer": target2["label"]
    })

    # Q3: Distractor Exclusion
    all_shown_ids = study_ids.union(loc_ids)
    never_shown_icons = [icon for icon in ICON_BANK if icon["id"] not in all_shown_ids]
    if len(never_shown_icons) < 1:
        never_shown_icons = non_study_icons
    target3 = random.choice(never_shown_icons)
    shown_icons = [icon for icon in ICON_BANK if icon["id"] in all_shown_ids]
    distractors3 = random.sample(shown_icons, min(3, len(shown_icons)))
    opts3 = [target3] + distractors3
    random.shuffle(opts3)
    questions.append({
        "question": "Which of these items was NOT shown in any of the earlier memory tasks?",
        "options": opts3,
        "answer": target3["label"]
    })

    # Q4: Contextual Association Recall
    target4_candidates = [icon for icon in study_icons if icon["id"] != target1["id"]]
    target4 = random.choice(target4_candidates) if target4_candidates else random.choice(study_icons)
    distractors4 = random.sample(non_study_icons, 3)
    opts4 = [target4] + distractors4
    random.shuffle(opts4)
    questions.append({
        "question": "Recall which item was studied alongside other objects in your memorization session:",
        "options": opts4,
        "answer": target4["label"]
    })

    return questions


RECOGNITION_ICONS = ICON_BANK[:8]

RECOGNITION_QUESTIONS = [
    {
        "question": "Which of these objects was presented in the memorization screen?",
        "options": [
            {"id": "car-front-fill", "label": "Car"},
            {"id": "bicycle", "label": "Bicycle"},
            {"id": "airplane-fill", "label": "Airplane"},
            {"id": "alarm-fill", "label": "Alarm Clock"},
        ],
        "answer": "Car",
    },
]

OBJECT_LOCATION_GAME_DATA = [
    [
        {"icon": {"id": "car-front-fill", "label": "Car"}, "position": 1},
        {"icon": {"id": "book-fill", "label": "Book"}, "position": 4},
        {"icon": {"id": "camera-fill", "label": "Camera"}, "position": 8},
    ],
]

DELAYED_RECALL_QUESTIONS = RECOGNITION_QUESTIONS
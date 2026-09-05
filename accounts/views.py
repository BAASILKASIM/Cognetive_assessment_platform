import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from .forms import ParticipantForm, LifestyleForm
from .models import AssessmentRecord
from .constants import (
    RECOGNITION_ICONS,
    RECOGNITION_QUESTIONS,
    OBJECT_LOCATION_GAME_DATA,
    DELAYED_RECALL_QUESTIONS,
    generate_recognition_data,
    generate_object_location_data,
    generate_delayed_recall_data,
)


def _safe_int(val, default=0):
    try:
        if val is None or val == "":
            return default
        return int(val)
    except (ValueError, TypeError):
        return default


def _safe_float(val, default=0.0):
    try:
        if val is None or val == "":
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


def home(request):
    return render(request, "accounts/home.html")


def instructions(request):
    return render(request, "accounts/instructions.html")


def compute_session_marks(request):
    """
    Extracts all participant details, lifestyle factors, and raw module scores from session.
    Calculates normalized scores, total memory score, composite cognitive score, and AI prediction.
    Synchronizes all computed values back into request.session.
    Returns a dictionary of structured marks and details.
    """
    name = request.session.get("name", "Participant")
    age = _safe_int(request.session.get("age"), 25)
    gender = request.session.get("gender", "Other")

    sleep_duration = _safe_float(request.session.get("sleep_duration"), 7.0)
    stress_level = _safe_int(request.session.get("stress_level"), 5)
    screen_time = str(request.session.get("screen_time", "4-6"))
    exercise_frequency = str(request.session.get("exercise_frequency", "Medium"))

    reaction_time = _safe_float(request.session.get("reaction_time"), 320.0)
    norm_reaction = max(0.0, min(100.0, 100.0 - ((reaction_time - 200.0) / 400.0) * 100.0))

    visual_memory_score = _safe_int(request.session.get("visual_memory_score"), 24)
    recognition_score = _safe_int(request.session.get("recognition_score"), 20)
    object_location_score = _safe_int(request.session.get("object_location_score"), 20)
    delayed_recall_score = _safe_int(request.session.get("delayed_recall_score"), 15)

    memory_score = visual_memory_score + recognition_score + object_location_score + delayed_recall_score
    memory_score = max(0, min(100, memory_score))

    clock_score = _safe_int(request.session.get("clock_score"), 16)
    clock_contour_score = _safe_int(request.session.get("clock_contour_score"), 4)
    clock_numbers_score = _safe_int(request.session.get("clock_numbers_score"), 6)
    clock_hands_score = _safe_int(request.session.get("clock_hands_score"), 6)
    clock_image_path = request.session.get("clock_image_path", "")

    norm_clock = (clock_score / 20.0) * 100.0

    cognitive_score = round((0.25 * norm_reaction) + (0.45 * memory_score) + (0.30 * norm_clock), 1)
    cognitive_score = max(0.0, min(100.0, cognitive_score))

    try:
        from ml.utils.predictor import predict_cognitive_score
        prediction = predict_cognitive_score({
            "age": age,
            "gender": gender,
            "sleep_duration": sleep_duration,
            "stress_level": stress_level,
            "screen_time": screen_time,
            "exercise_frequency": exercise_frequency,
            "reaction_time": reaction_time,
            "memory_score": memory_score,
        })
        ai_predicted_score = prediction.get("ai_predicted_score", cognitive_score)
        performance_tier = prediction.get("performance_tier", "Normal")
    except Exception:
        ai_predicted_score = cognitive_score
        performance_tier = "Normal"

    # Synchronize all calculated marks into session
    request.session["name"] = name
    request.session["age"] = age
    request.session["gender"] = gender
    request.session["sleep_duration"] = sleep_duration
    request.session["stress_level"] = stress_level
    request.session["screen_time"] = screen_time
    request.session["exercise_frequency"] = exercise_frequency
    request.session["reaction_time"] = reaction_time
    request.session["reaction_score"] = round(norm_reaction, 1)
    request.session["visual_memory_score"] = visual_memory_score
    request.session["recognition_score"] = recognition_score
    request.session["object_location_score"] = object_location_score
    request.session["delayed_recall_score"] = delayed_recall_score
    request.session["memory_score"] = memory_score
    request.session["clock_score"] = clock_score
    request.session["clock_contour_score"] = clock_contour_score
    request.session["clock_numbers_score"] = clock_numbers_score
    request.session["clock_hands_score"] = clock_hands_score
    request.session["norm_clock"] = round(norm_clock, 1)
    request.session["cognitive_score"] = cognitive_score
    request.session["ai_predicted_score"] = ai_predicted_score
    request.session["performance_tier"] = performance_tier

    return {
        "name": name,
        "age": age,
        "gender": gender,
        "sleep_duration": sleep_duration,
        "stress_level": stress_level,
        "screen_time": screen_time,
        "exercise_frequency": exercise_frequency,
        "reaction_time": reaction_time,
        "norm_reaction": round(norm_reaction, 1),
        "visual_memory_score": visual_memory_score,
        "recognition_score": recognition_score,
        "object_location_score": object_location_score,
        "delayed_recall_score": delayed_recall_score,
        "memory_score": memory_score,
        "clock_score": clock_score,
        "clock_contour_score": clock_contour_score,
        "clock_numbers_score": clock_numbers_score,
        "clock_hands_score": clock_hands_score,
        "norm_clock": round(norm_clock, 1),
        "clock_image_path": clock_image_path,
        "cognitive_score": cognitive_score,
        "ai_predicted_score": ai_predicted_score,
        "performance_tier": performance_tier,
    }


def session_debug(request):
    marks = compute_session_marks(request)
    if request.GET.get("format") == "json" or "application/json" in request.headers.get("Accept", ""):
        return JsonResponse(dict(request.session))

    session_json = json.dumps(dict(request.session), indent=4)
    return render(
        request,
        "accounts/debug.html",
        {
            "marks": marks,
            "session_data": dict(request.session),
            "session_json": session_json,
        },
    )


# Participant Information
def participant(request):
    if request.method == "POST":
        form = ParticipantForm(request.POST)
        if form.is_valid():
            request.session["name"] = form.cleaned_data["name"]
            request.session["age"] = form.cleaned_data["age"]
            request.session["gender"] = form.cleaned_data["gender"]
            return redirect("lifestyle")
    else:
        form = ParticipantForm()

    return render(
        request,
        "accounts/participant.html",
        {
            "form": form,
            "current_step": 1,
            "progress": 17,
        },
    )


# Lifestyle Assessment
def lifestyle(request):
    if request.method == "POST":
        form = LifestyleForm(request.POST)
        if form.is_valid():
            request.session["sleep_duration"] = form.cleaned_data["sleep_duration"]
            request.session["stress_level"] = form.cleaned_data["stress_level"]
            request.session["screen_time"] = form.cleaned_data["screen_time"]
            request.session["exercise_frequency"] = form.cleaned_data["exercise_frequency"]
            return redirect("reaction_test")
    else:
        form = LifestyleForm()

    return render(
        request,
        "accounts/lifestyle.html",
        {
            "form": form,
            "current_step": 2,
            "progress": 33,
        },
    )


# Reaction Time Test
def reaction_test(request):
    return render(
        request,
        "accounts/reaction_test.html",
        {
            "current_step": 3,
            "progress": 50,
        },
    )


def save_reaction(request):
    if request.method == "POST":
        data = json.loads(request.body)
        rt = _safe_float(data.get("reaction_time"), 320.0)
        request.session["reaction_time"] = rt
        norm_reaction = max(0.0, min(100.0, 100.0 - ((rt - 200.0) / 400.0) * 100.0))
        request.session["reaction_score"] = round(norm_reaction, 1)
        compute_session_marks(request)
        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error"}, status=400)


# Memory Test Page (Step 1: Visual Memory Grid)
def memory_test(request):
    return render(
        request,
        "accounts/memory_test.html",
        {
            "current_step": 4,
            "progress": 60,
            "memory_step": 1,
        },
    )


# Save Visual Memory Score
def save_visual_memory(request):
    if request.method == "POST":
        data = json.loads(request.body)
        score = _safe_int(data.get("visual_memory_score"), 0)
        request.session["visual_memory_score"] = score
        compute_session_marks(request)
        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error"}, status=400)


# Step 2: Recognition Memory
def recognition_memory(request):
    study_icons = request.session.get("recognition_study_icons")
    questions = request.session.get("recognition_questions")
    if not study_icons or not questions:
        study_icons, questions = generate_recognition_data()
        request.session["recognition_study_icons"] = study_icons
        request.session["recognition_questions"] = questions

    return render(
        request,
        "accounts/recognition_memory.html",
        {
            "current_step": 4,
            "progress": 70,
            "memory_step": 2,
            "icons": study_icons,
            "questions": questions,
        },
    )


def save_recognition_memory(request):
    if request.method == "POST":
        data = json.loads(request.body)
        score = _safe_int(data.get("recognition_score"), 0)
        request.session["recognition_score"] = score
        compute_session_marks(request)
        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error"}, status=400)


# Step 3: Object Location Memory
def object_location_memory(request):
    game_data = request.session.get("object_location_game_data")
    if not game_data:
        game_data = generate_object_location_data()
        request.session["object_location_game_data"] = game_data

    return render(
        request,
        "accounts/object_location_memory.html",
        {
            "current_step": 4,
            "progress": 75,
            "memory_step": 3,
            "game_data": game_data,
        },
    )


def save_object_location(request):
    if request.method == "POST":
        data = json.loads(request.body)
        score = _safe_int(data.get("object_location_score"), 0)
        request.session["object_location_score"] = score
        compute_session_marks(request)
        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error"}, status=400)


# Step 4: Delayed Recall Memory
def delayed_recall(request):
    study_icons = request.session.get("recognition_study_icons")
    game_data = request.session.get("object_location_game_data")
    questions = generate_delayed_recall_data(study_icons, game_data)
    request.session["delayed_recall_questions"] = questions

    return render(
        request,
        "accounts/delayed_recall.html",
        {
            "current_step": 4,
            "progress": 80,
            "memory_step": 4,
            "questions": questions,
        },
    )


def save_delayed_recall(request):
    if request.method == "POST":
        data = json.loads(request.body)
        score = _safe_int(data.get("delayed_recall_score"), 0)
        request.session["delayed_recall_score"] = score

        marks = compute_session_marks(request)

        return JsonResponse({
            "status": "success",
            "delayed_recall_score": score,
            "visual_memory_score": marks["visual_memory_score"],
            "recognition_score": marks["recognition_score"],
            "object_location_score": marks["object_location_score"],
            "total_memory_score": marks["memory_score"]
        })

    return JsonResponse({"status": "error"}, status=400)


# Clock Drawing Test Page
def clock_test(request):
    return render(
        request,
        "accounts/clock_test.html",
        {
            "current_step": 5,
            "progress": 85,
        },
    )


# Save and Analyze Clock Drawing Test (Computer Vision)
def save_clock_test(request):
    if request.method == "POST":
        data = json.loads(request.body)
        image_data = data.get("image_data")

        if not image_data:
            return JsonResponse({"status": "error", "message": "No image data provided"}, status=400)

        from .cv_analyzer import save_base64_clock_image, analyze_clock_drawing

        # Save image file to media directory
        rel_path, abs_path = save_base64_clock_image(image_data, settings.MEDIA_ROOT)

        # Run Computer Vision analysis
        analysis = analyze_clock_drawing(abs_path)

        # Store in session
        request.session["clock_score"] = analysis["clock_score"]
        request.session["clock_image_path"] = rel_path
        request.session["clock_contour_score"] = analysis["contour_score"]
        request.session["clock_numbers_score"] = analysis["numbers_score"]
        request.session["clock_hands_score"] = analysis["hands_score"]
        norm_clock = (analysis["clock_score"] / 20.0) * 100.0
        request.session["norm_clock"] = round(norm_clock, 1)

        return JsonResponse({
            "status": "success",
            "clock_score": analysis["clock_score"],
            "contour_score": analysis["contour_score"],
            "numbers_score": analysis["numbers_score"],
            "hands_score": analysis["hands_score"],
            "feedback": analysis["feedback"],
            "image_url": f"{settings.MEDIA_URL}{rel_path}"
        })

    return JsonResponse({"status": "error"}, status=400)


# Retake Assessment
def retake_assessment(request):
    keys_to_clear = [
        "name", "age", "gender", "sleep_duration", "stress_level",
        "screen_time", "exercise_frequency", "reaction_time", "reaction_score",
        "visual_memory_score", "recognition_score", "object_location_score",
        "delayed_recall_score", "memory_score", "clock_score",
        "clock_contour_score", "clock_numbers_score", "clock_hands_score",
        "norm_clock", "cognitive_score", "ai_predicted_score", "performance_tier",
        "clock_image_path", "assessment_record_id",
        "recognition_study_icons", "recognition_questions",
        "object_location_game_data", "delayed_recall_questions"
    ]
    for key in keys_to_clear:
        request.session.pop(key, None)
    return redirect("instructions")


def generate_recommendations(record):
    """
    Analyzes lifestyle factors and cognitive test scores to produce personalized,
    actionable improvement recommendations for both daily lifestyle and game performance.
    """
    lifestyle_recs = []
    cognitive_recs = []

    # 1. Sleep Analysis
    if record.sleep_duration < 7.0:
        lifestyle_recs.append({
            "category": "Sleep & Recovery",
            "title": "Insufficient Sleep Duration",
            "status": "Attention Needed",
            "badge_class": "bg-danger-subtle text-danger border-danger",
            "icon": "bi-moon-stars-fill",
            "icon_color": "text-danger",
            "observation": f"Current sleep duration ({record.sleep_duration}h/night) is below the recommended 7.5–8.5 hours.",
            "suggestion": "Target 7.5 to 8.5 hours of continuous restorative sleep. Sleep deprivation directly degrades hippocampal short-term memory consolidation and slows neural response speed.",
        })
    elif record.sleep_duration > 9.0:
        lifestyle_recs.append({
            "category": "Sleep & Recovery",
            "title": "Extended Sleep Duration",
            "status": "Optimization",
            "badge_class": "bg-warning-subtle text-warning border-warning",
            "icon": "bi-moon-stars-fill",
            "icon_color": "text-warning",
            "observation": f"Sleep duration ({record.sleep_duration}h/night) is slightly above typical baseline.",
            "suggestion": "Maintain a regular sleep-wake schedule and incorporate morning physical activity to optimize daytime alertness.",
        })
    else:
        lifestyle_recs.append({
            "category": "Sleep & Recovery",
            "title": "Optimal Sleep Baseline",
            "status": "Good Baseline",
            "badge_class": "bg-success-subtle text-success border-success",
            "icon": "bi-moon-stars-fill",
            "icon_color": "text-success",
            "observation": f"Healthy sleep duration of {record.sleep_duration}h/night.",
            "suggestion": "Maintain your consistent sleep routine. Restorative sleep supports synaptic plasticity and long-term memory retrieval.",
        })

    # 2. Stress Level Analysis
    if record.stress_level >= 7:
        lifestyle_recs.append({
            "category": "Stress Management",
            "title": "High Stress Index Detected",
            "status": "High Priority",
            "badge_class": "bg-danger-subtle text-danger border-danger",
            "icon": "bi-heart-pulse-fill",
            "icon_color": "text-danger",
            "observation": f"Reported stress index is high ({record.stress_level}/10).",
            "suggestion": "Elevated cortisol levels impair prefrontal cortex agility and reaction speed. Practice daily 10-minute box breathing (4-4-4-4 technique) or mindfulness meditation.",
        })
    elif record.stress_level >= 5:
        lifestyle_recs.append({
            "category": "Stress Management",
            "title": "Moderate Stress Level",
            "status": "Monitoring Advised",
            "badge_class": "bg-warning-subtle text-warning border-warning",
            "icon": "bi-heart-pulse-fill",
            "icon_color": "text-warning",
            "observation": f"Stress level is at a moderate baseline ({record.stress_level}/10).",
            "suggestion": "Take short 5-minute mental reset breaks during work and try light stretching or breathing exercises to prevent cognitive fatigue.",
        })
    else:
        lifestyle_recs.append({
            "category": "Stress Management",
            "title": "Optimal Stress Resilience",
            "status": "Optimal",
            "badge_class": "bg-success-subtle text-success border-success",
            "icon": "bi-heart-pulse-fill",
            "icon_color": "text-success",
            "observation": f"Healthy low stress index ({record.stress_level}/10).",
            "suggestion": "Excellent stress management! Balanced cortisol levels foster steady neurotransmitter equilibrium and clear focus.",
        })

    # 3. Physical Activity Analysis
    exercise_lower = str(record.exercise_frequency).lower()
    if exercise_lower in ["low", "none", "rarely", "sedentary"]:
        lifestyle_recs.append({
            "category": "Physical Fitness",
            "title": "Low Physical Exercise Frequency",
            "status": "Action Required",
            "badge_class": "bg-warning-subtle text-warning border-warning",
            "icon": "bi-activity",
            "icon_color": "text-warning",
            "observation": f"Exercise frequency is listed as '{record.exercise_frequency}'.",
            "suggestion": "Aim for at least 150 minutes of moderate aerobic exercise per week (e.g. brisk walking, cycling). Physical exercise boosts BDNF (Brain-Derived Neurotrophic Factor), encouraging neurogenesis and spatial memory retention.",
        })
    else:
        lifestyle_recs.append({
            "category": "Physical Fitness",
            "title": "Active Physical Lifestyle",
            "status": "Optimal",
            "badge_class": "bg-success-subtle text-success border-success",
            "icon": "bi-activity",
            "icon_color": "text-success",
            "observation": f"Good physical activity routine ('{record.exercise_frequency}').",
            "suggestion": "Continue regular workouts! Physical activity promotes cerebral blood flow and protects against cognitive decline.",
        })

    # 4. Screen Time Analysis
    screen_str = str(record.screen_time).lower()
    if any(x in screen_str for x in [">8", "8+", "6-8", ">6"]):
        lifestyle_recs.append({
            "category": "Digital Wellness",
            "title": "High Screen Time Exposure",
            "status": "Eye Strain Warning",
            "badge_class": "bg-info-subtle text-dark border-info",
            "icon": "bi-display",
            "icon_color": "text-info",
            "observation": f"Extended screen exposure ({record.screen_time} hours/day).",
            "suggestion": "Follow the 20-20-20 rule (every 20 mins, look at something 20 feet away for 20 seconds). Avoid screens 1 hour before bedtime to prevent blue light disruption of sleep.",
        })

    # ----------------------------------------------------
    # Cognitive Game Modules Analysis
    # ----------------------------------------------------

    # Sensorimotor Latency / Reaction Speed
    norm_reaction = record.reaction_score
    if norm_reaction < 65.0 or record.reaction_time > 340.0:
        cognitive_recs.append({
            "category": "Reflex Speed",
            "title": "Sensorimotor Latency Improvement",
            "status": "Speed Training",
            "badge_class": "bg-danger-subtle text-danger border-danger",
            "icon": "bi-lightning-charge-fill",
            "icon_color": "text-warning",
            "score_str": f"{record.reaction_time:.0f} ms ({norm_reaction:.1f}%)",
            "observation": f"Visual-motor reflex response latency is slower than average baseline ({record.reaction_time:.0f} ms).",
            "suggestion": "Practice fast visual-tracking games, dual-task reaction exercises, or racquet sports (table tennis, badminton) to enhance visual stimulus processing and neuromuscular response speed.",
        })
    else:
        cognitive_recs.append({
            "category": "Reflex Speed",
            "title": "Sharp Reflex Latency",
            "status": "High Performance",
            "badge_class": "bg-success-subtle text-success border-success",
            "icon": "bi-lightning-charge-fill",
            "icon_color": "text-success",
            "score_str": f"{record.reaction_time:.0f} ms ({norm_reaction:.1f}%)",
            "observation": f"Optimal reflex response latency ({record.reaction_time:.0f} ms).",
            "suggestion": "Maintain your rapid visual-motor reflexes with quick decision-making challenges.",
        })

    # Visual Pattern Memory
    pct_visual = (record.visual_memory_score / 30.0) * 100.0
    if pct_visual < 70.0:
        cognitive_recs.append({
            "category": "Visual Pattern Memory",
            "title": "Visual Memory Grid Enhancement",
            "status": "Train Pattern Recall",
            "badge_class": "bg-warning-subtle text-warning border-warning",
            "icon": "bi-grid-3x3-gap-fill",
            "icon_color": "text-primary",
            "score_str": f"{record.visual_memory_score}/30 ({pct_visual:.0f}%)",
            "observation": f"Visual pattern reconstruction score was below optimal ({record.visual_memory_score}/30).",
            "suggestion": "Practice visual 'chunking' techniques—grouping adjacent grid squares into familiar shapes (triangles, lines) rather than memorizing single cells individually.",
        })

    # Recognition Memory
    pct_rec = (record.recognition_score / 25.0) * 100.0
    if pct_rec < 72.0:
        cognitive_recs.append({
            "category": "Object Recognition",
            "title": "Recognition Precision Training",
            "status": "Focus Retention",
            "badge_class": "bg-warning-subtle text-warning border-warning",
            "icon": "bi-eye-fill",
            "icon_color": "text-info",
            "score_str": f"{record.recognition_score}/25 ({pct_rec:.0f}%)",
            "observation": f"Object recognition accuracy showed room for improvement ({record.recognition_score}/25).",
            "suggestion": "When studying items, use active verbal labeling (e.g. naming item features aloud) to dual-encode items in both visual and verbal memory stores.",
        })

    # Spatial Location Memory
    pct_loc = (record.object_location_score / 25.0) * 100.0
    if pct_loc < 72.0:
        cognitive_recs.append({
            "category": "Spatial Location Memory",
            "title": "Spatial-Association Memory Training",
            "status": "Spatial Practice",
            "badge_class": "bg-warning-subtle text-warning border-warning",
            "icon": "bi-geo-alt-fill",
            "icon_color": "text-success",
            "score_str": f"{record.object_location_score}/25 ({pct_loc:.0f}%)",
            "observation": f"Spatial item placement accuracy scored {record.object_location_score}/25.",
            "suggestion": "Utilize spatial anchor points (corner vs center grid positions) or the Method of Loci (Memory Palace) to pair item identity with specific spatial coordinates.",
        })

    # Delayed Recall Memory
    pct_del = (record.delayed_recall_score / 20.0) * 100.0
    if pct_del < 70.0:
        cognitive_recs.append({
            "category": "Delayed Recall",
            "title": "Long-Term Retrieval Enhancement",
            "status": "Retrieval Practice",
            "badge_class": "bg-danger-subtle text-danger border-danger",
            "icon": "bi-clock-history",
            "icon_color": "text-danger",
            "score_str": f"{record.delayed_recall_score}/20 ({pct_del:.0f}%)",
            "observation": f"Delayed retrieval of earlier items scored {record.delayed_recall_score}/20.",
            "suggestion": "Engage in spaced repetition practice: review newly learned information at 15-minute and 1-hour intervals to strengthen hippocampal-cortical retrieval pathways.",
        })

    # Clock Drawing Test (Visuospatial / Executive)
    pct_clock = (record.clock_score / 20.0) * 100.0
    if pct_clock < 75.0:
        cognitive_recs.append({
            "category": "Visuospatial Construction (CDT)",
            "title": "Executive Planning & Spatial Drawing",
            "status": "Executive Practice",
            "badge_class": "bg-warning-subtle text-warning border-warning",
            "icon": "bi-pencil-square",
            "icon_color": "text-purple",
            "score_str": f"{record.clock_score}/20 ({pct_clock:.0f}%)",
            "observation": f"Clock Drawing Test score ({record.clock_score}/20) indicates slight executive/spatial planning difficulty.",
            "suggestion": "Engage in spatial construction activities (3D modeling, drawing, maze navigation, Sudoku) to stimulate parietal lobe visuospatial coordination and frontal lobe planning.",
        })

    # If all cognitive tests are high, add a praise/maintenance recommendation!
    if not any(r["status"] != "High Performance" for r in cognitive_recs):
        cognitive_recs.append({
            "category": "Overall Mastery",
            "title": "Peak Cognitive Performance",
            "status": "Optimal",
            "badge_class": "bg-success-subtle text-success border-success",
            "icon": "bi-trophy-fill",
            "icon_color": "text-warning",
            "score_str": f"{record.cognitive_score:.1f}/100",
            "observation": "All cognitive test sub-modules demonstrated high accuracy and speed.",
            "suggestion": "Outstanding performance across all domains! Continue challenging your brain with novel learning, complex problem solving, and an active healthy lifestyle.",
        })

    return {
        "lifestyle_recs": lifestyle_recs,
        "cognitive_recs": cognitive_recs,
        "attention_needed_count": sum(1 for r in lifestyle_recs + cognitive_recs if any(k in r["status"] for k in ["Attention", "Action", "High Priority", "Training", "Improvement", "Practice", "Warning"])),
    }


# Final Cognitive Assessment Report
def report(request):
    marks = compute_session_marks(request)

    # Database Persistence: Save ONE complete record if not already saved in session
    saved_record_id = request.session.get("assessment_record_id")

    record = None
    if saved_record_id:
        try:
            record = AssessmentRecord.objects.get(id=saved_record_id)
        except AssessmentRecord.DoesNotExist:
            record = None

    if record is None:
        record = AssessmentRecord.objects.create(
            name=marks["name"],
            age=marks["age"],
            gender=marks["gender"],
            sleep_duration=marks["sleep_duration"],
            stress_level=marks["stress_level"],
            screen_time=marks["screen_time"],
            exercise_frequency=marks["exercise_frequency"],
            reaction_time=marks["reaction_time"],
            reaction_score=marks["norm_reaction"],
            visual_memory_score=marks["visual_memory_score"],
            recognition_score=marks["recognition_score"],
            object_location_score=marks["object_location_score"],
            delayed_recall_score=marks["delayed_recall_score"],
            memory_score=marks["memory_score"],
            clock_score=marks["clock_score"],
            clock_contour_score=marks["clock_contour_score"],
            clock_numbers_score=marks["clock_numbers_score"],
            clock_hands_score=marks["clock_hands_score"],
            clock_image=marks["clock_image_path"],
            cognitive_score=marks["cognitive_score"],
            ai_predicted_score=marks["ai_predicted_score"],
            performance_tier=marks["performance_tier"],
        )
        request.session["assessment_record_id"] = record.id
    else:
        # Synchronize existing record with freshly computed marks
        record.name = marks["name"]
        record.age = marks["age"]
        record.gender = marks["gender"]
        record.sleep_duration = marks["sleep_duration"]
        record.stress_level = marks["stress_level"]
        record.screen_time = marks["screen_time"]
        record.exercise_frequency = marks["exercise_frequency"]
        record.reaction_time = marks["reaction_time"]
        record.reaction_score = marks["norm_reaction"]
        record.visual_memory_score = marks["visual_memory_score"]
        record.recognition_score = marks["recognition_score"]
        record.object_location_score = marks["object_location_score"]
        record.delayed_recall_score = marks["delayed_recall_score"]
        record.memory_score = marks["memory_score"]
        record.clock_score = marks["clock_score"]
        record.clock_contour_score = marks["clock_contour_score"]
        record.clock_numbers_score = marks["clock_numbers_score"]
        record.clock_hands_score = marks["clock_hands_score"]
        record.clock_image = marks["clock_image_path"]
        record.cognitive_score = marks["cognitive_score"]
        record.ai_predicted_score = marks["ai_predicted_score"]
        record.performance_tier = marks["performance_tier"]
        record.save()

    pct_visual = round((record.visual_memory_score / 30.0) * 100.0, 1)
    pct_recognition = round((record.recognition_score / 25.0) * 100.0, 1)
    pct_location = round((record.object_location_score / 25.0) * 100.0, 1)
    pct_delayed = round((record.delayed_recall_score / 20.0) * 100.0, 1)

    pct_clock_contour = round((record.clock_contour_score / 4.0) * 100.0, 1)
    pct_clock_numbers = round((record.clock_numbers_score / 8.0) * 100.0, 1)
    pct_clock_hands = round((record.clock_hands_score / 8.0) * 100.0, 1)

    norm_reaction = round(record.reaction_score, 1)
    norm_clock = round((record.clock_score / 20.0) * 100.0, 1)

    recommendations_data = generate_recommendations(record)

    tier_map = {
        "High Performance": {
            "badge_class": "bg-success text-white",
            "icon": "bi-trophy-fill",
            "summary": "Optimal cognitive functionality with superior processing speed and recall accuracy.",
        },
        "Normal": {
            "badge_class": "bg-primary text-white",
            "icon": "bi-check-circle-fill",
            "summary": "Cognitive performance is within normal neuro-baseline expectations across all modules.",
        },
        "Mild Impairment Risk": {
            "badge_class": "bg-warning text-dark",
            "icon": "bi-exclamation-triangle-fill",
            "summary": "Slight deviations detected in speed or spatial-memory retrieval. Periodic monitoring advised.",
        },
    }
    tier_config = tier_map.get(record.performance_tier, tier_map["Normal"])

    chart_data = {
        "radar": {
            "labels": [
                "Visual Pattern",
                "Recognition",
                "Object Location",
                "Delayed Recall",
                "Reflex Speed",
                "Clock Test",
            ],
            "user_scores": [
                pct_visual,
                pct_recognition,
                pct_location,
                pct_delayed,
                norm_reaction,
                norm_clock,
            ],
            "norm_scores": [75, 75, 75, 75, 75, 75],
        },
        "bar": {
            "labels": [
                "Reflex Latency",
                "Memory Composite",
                "Visuospatial CDT",
                "Neuro Composite",
                "AI ML Prediction",
            ],
            "scores": [
                norm_reaction,
                record.memory_score,
                norm_clock,
                record.cognitive_score,
                record.ai_predicted_score,
            ],
        },
    }

    return render(
        request,
        "accounts/report.html",
        {
            "record": record,
            "pct_visual": pct_visual,
            "pct_recognition": pct_recognition,
            "pct_location": pct_location,
            "pct_delayed": pct_delayed,
            "pct_clock_contour": pct_clock_contour,
            "pct_clock_numbers": pct_clock_numbers,
            "pct_clock_hands": pct_clock_hands,
            "norm_reaction": norm_reaction,
            "norm_clock": norm_clock,
            "tier_config": tier_config,
            "chart_data": chart_data,
            "lifestyle_recs": recommendations_data["lifestyle_recs"],
            "cognitive_recs": recommendations_data["cognitive_recs"],
            "attention_needed_count": recommendations_data["attention_needed_count"],
        },
    )
from django.db import models

class CognitiveQuestion(models.Model):
    CATEGORY_CHOICES = [
        ('REASONING', 'Logical Reasoning'),
        ('MEMORY', 'Memory Recall'),
    ]
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    question_text = models.TextField()
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_option = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])

    def __str__(self):
        return f"[{self.category}] {self.question_text[:30]}..."


class AssessmentRecord(models.Model):
    """
    Stores ONE complete assessment record upon completion of all modules:
    Participant -> Lifestyle -> Reaction -> Memory (4 submodules) -> Clock (CV) -> AI Prediction
    """
    # Participant Info
    name = models.CharField(max_length=150)
    age = models.IntegerField()
    gender = models.CharField(max_length=20)

    # Lifestyle Factors
    sleep_duration = models.FloatField(default=7.0)
    stress_level = models.IntegerField(default=5)
    screen_time = models.CharField(max_length=50, default="4-6")
    exercise_frequency = models.CharField(max_length=50, default="Medium")

    # Reaction Test
    reaction_time = models.FloatField(help_text="Reaction time in milliseconds")
    reaction_score = models.FloatField(default=0.0, help_text="Normalized Reaction Score / 100")

    # Memory Test Submodules
    visual_memory_score = models.IntegerField(default=0, help_text="Visual Pattern Score / 30")
    recognition_score = models.IntegerField(default=0, help_text="Recognition Memory Score / 25")
    object_location_score = models.IntegerField(default=0, help_text="Object Location Score / 25")
    delayed_recall_score = models.IntegerField(default=0, help_text="Delayed Recall Score / 20")
    memory_score = models.IntegerField(default=0, help_text="Combined Total Memory Score / 100")

    # Clock Drawing Test
    clock_score = models.IntegerField(default=0, help_text="Clock Test Score / 20")
    clock_contour_score = models.IntegerField(default=0, help_text="Contour / 4")
    clock_numbers_score = models.IntegerField(default=0, help_text="Numbers / 8")
    clock_hands_score = models.IntegerField(default=0, help_text="Hands / 8")
    clock_image = models.CharField(max_length=255, null=True, blank=True, help_text="Path to drawing image")

    # Composite & AI Predicted Scores
    cognitive_score = models.FloatField(help_text="Calculated Overall Cognitive Score / 100")
    ai_predicted_score = models.FloatField(help_text="AI Predicted Cognitive Score / 100")
    performance_tier = models.CharField(max_length=100, default="Normal")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Assessment for {self.name} ({self.age}y, {self.gender}) - Score: {self.cognitive_score:.1f}/100 [AI: {self.ai_predicted_score:.1f}] on {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ["-created_at"]
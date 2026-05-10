from __future__ import annotations


INTAKE_QUESTIONS = [
    {
        "id": "age_group",
        "label": "Select your age group",
        "options": ["Under_18", "18_24", "25_34", "35_44", "45_54", "55_plus"],
    },
    {
        "id": "gender",
        "label": "Gender identity",
        "options": ["Male", "Female", "Non_binary"],
    },
    {
        "id": "therapy_status",
        "label": "Are you currently seeing a mental health professional?",
        "options": ["Yes", "No"],
    },
    {
        "id": "main_issue",
        "label": "What is the primary reason you are seeking guidance today?",
        "options": ["Anxiety_Worry_or_Panic", "Depression_or_Low_Mood", "Sleep_Issues_or_Fatigue", "Relationship_or_Family_Conflicts", "Trauma_or_Grief", "Work_Stress_or_Burnout", "Other"],
    },
    {
        "id": "duration",
        "label": "How long have you been experiencing this?",
        "options": ["Less_than_2_weeks_(Acute)", "Between_2_to_8_weeks", "Over_6_months_(Chronic)", "Off_and_on_for_years"],
    },
    {
        "id": "impact",
        "label": "To what degree is this impairing your daily functioning (work, social, self-care)?",
        "options": ["Mild_I_can_mostly_function_normally", "Moderate_It_is_making_daily_tasks_difficult", "Severe_I_am_struggling_to_function"],
    },
    {
        "id": "help_type",
        "label": "What kind of help would feel most useful right now?",
        "options": ["Practical_Coping_Steps", "Source_Backed_Explanation", "Emotional_Support", "Reflection_and_Self_Understanding"],
    },
    {
        "id": "communication_style",
        "label": "How would you like responses to feel?",
        "options": ["Warm_and_Gentle", "Direct_and_Practical", "Structured_and_Analytical"],
    },
    {
        "id": "response_length_preference",
        "label": "What response length works best for you?",
        "options": ["Very_Short", "Balanced", "Detailed"],
    },
    {
        "id": "coping_style",
        "label": "What usually helps you most when stress rises?",
        "options": ["Breathing_or_Grounding", "Talking_to_Someone", "Writing_or_Journaling", "Action_Plan_or_Checklist", "I_am_not_Sure_Yet"],
    }
]


def normalize_intake(raw: dict[str, str]) -> dict[str, str]:
    fields = [
        "age_group",
        "gender",
        "therapy_status",
        "main_issue",
        "duration",
        "impact",
        "help_type",
        "communication_style",
        "response_length_preference",
        "coping_style",
        "safety_concern",
    ]
    intake = {key: "" for key in fields}
    intake.update({key: value for key, value in raw.items() if value is not None})
    intake["complete"] = "true"
    return intake

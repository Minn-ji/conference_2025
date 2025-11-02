from utils import get_user_info, get_recent_quiz_info, get_recent_planner


def create_planner_input_payload(student_id: str, date: str):
    '''create planner about per day.'''
    user_info = get_user_info(student_id)
    quiz_info = get_recent_quiz_info(student_id) # quiz_id, quizes, total_score
    planner = get_recent_planner(student_id)

    return {
        "grade": user_info["grade"],
        "available_time_min": user_info["study_hours"]*60, # convert to minutes
        "initial_level": user_info["soup"],
        "recent_quiz_info": quiz_info,
        "recent_planner": planner
    }


def create_eval_quiz_input_payload(request):
    pass
#     all_quizzes = request.quizzes
#     for quiz in all_quizzes:
#         question = quiz["question"]
#         answer = quiz["answer"]
#         user_answer = quiz["user_answer"]
        

#         quiz_payload = {
#             "question": ["query"],
#             "answer": ["predicted_documents"],
#             "user_answer": cleanseddata["ground_truth_documents"], # List[List of text]
#             "ans_by_level": "",

#         }
#     final_payload = {
#         "retrieve_metrics": config["retrieve_metrics"],
#         "dataset": {
#             "Retrieval": retrieval_dataset,
#         },
#             "evaluation_mode": config["evaluation_mode"],
#     }

#     return final_payload

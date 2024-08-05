import random
from django.shortcuts import get_object_or_404, render, HttpResponse, redirect
from django.urls import reverse
from quiz.forms import ProfileUpdateForm, QuizForm
from django.db.models import Count, Sum
from . models import *
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from urllib.parse import quote
from django.contrib.auth.forms import UserChangeForm
import uuid

# Create your views here.


@login_required
def index(request):
    user = request.user

    # List of attempted quizzes
    attempted_quizzes = Quiz.objects.filter(
        user=user, given_question__isnull=False).distinct().order_by('-end_time')[:5] or None

    # Top 5 activities
    last_login_time = User.objects.filter(
        pk=request.user.pk).values_list('last_login', flat=True).first() or None

    # Get the latest course in Quiz
    latest_course = Quiz.objects.filter(
        user=request.user).order_by('-end_time').first() or None

    # Get the latest Category added
    latest_category = Category.objects.order_by('-created_at').first() or None

    # Number of courses, enrolled courses, and completed courses
    total_courses = Category.objects.count() or 0
    enrolled_courses = Quiz.objects.filter(user=user).count() or 0
    completed_courses = Quiz.objects.filter(
        user=user, end_time__isnull=False).count() or 0
    quizzes = Quiz.objects.filter(user=request.user) or []

    # Initialize totals
    total_questions = 0
    total_answered = 0
    total_correct = 0
    total_wrong = 0

    for quiz in quizzes:
        data = quiz.get_total_answered_questions_across_all_categories()
        total_questions += data.get('all_questions', 0)
        total_answered += data.get('total_answered', 0)
        total_correct += data.get('total_correct', 0)
        total_wrong += data.get('total_wrong', 0)

    total_remaining = total_questions - total_answered

    context = {
        'attempted_quizzes': attempted_quizzes,
        'last_login_time': last_login_time,
        'latest_course': latest_course,
        'latest_category': latest_category,
        'total_courses': total_courses,
        'total_questions': total_questions,
        'total_answered': total_answered,
        'total_remaining': total_remaining,
        'enrolled_courses': enrolled_courses,
        'completed_courses': completed_courses,
        'total_correct': total_correct,
        'total_wrong': total_wrong,

    }

    return render(request, 'dashboard/index.html', context)


@login_required
def check_answer(request, uid, createObj):
    try:
        payload = {'status': 200}
        answer = Answer.objects.get(uid=str(uid))
        if createObj == 'true':
            question = GivenQuizQuestions.objects.get_or_create(
                question=answer.question, answer=answer)[0]
            quiz = Quiz.objects.get(
                user=request.user, topic=answer.question.category)
            is_already_given = Quiz.objects.filter(
                Q(user=request.user) & Q(
                    given_question__question=question.question)
            ).exists()

            if not is_already_given:
                quiz.given_question.add(question)
                quiz.save()
            else:
                payload = {'status': 404}
            payload['marks'] = quiz.marks
        else:
            payload = {'status': 404}
        if answer.is_correct:
            payload['is_correct'] = 'true'
        else:
            payload['is_correct'] = 'false'

        return JsonResponse(payload)
    except Exception as e:

        return JsonResponse({'status': 404})


def calculate_marks(quiz):
    # Implement the logic to calculate the total marks
    # For example:
    total_marks = 0
    for given_question in quiz.given_question.all():
        if given_question.answer.is_correct:
            total_marks += given_question.question.mark
    return total_marks


# def quiz(request):
#     if request.method == 'POST':
#         form = QuizForm(request.POST, topics_choices=[
#             (topic, topic) for topic in Question.objects.values_list('topic', flat=True).distinct()
#         ])
#         if form.is_valid():
#             selected_topics = form.cleaned_data['topics']
#             question_limit = form.cleaned_data['num_questions']
#             quiz_mode = form.cleaned_data['quiz_mode']

#             if selected_topics:
#                 questions = Question.objects.filter(
#                     topic__in=selected_topics
#                 ).distinct()[:question_limit]

#                 if not questions.exists():
#                     return HttpResponse("No questions found for selected topics.")

#                 quiz, created = Quiz.objects.get_or_create(
#                     user=request.user, defaults={'total_marks': 0, 'marks': 0}
#                 )
#                 paginator = Paginator(questions, 1)
#                 page_number = request.GET.get('page')

#                 try:
#                     page_obj = paginator.page(page_number)
#                 except PageNotAnInteger:
#                     page_obj = paginator.page(1)
#                 except EmptyPage:
#                     page_obj = paginator.page(paginator.num_pages)

#                 # Handling answer submission
#                 if 'submit' in request.POST:
#                     question = page_obj.object_list[0]
#                     answer_id = request.POST.get(
#                         f'answer_{page_obj.object_list[0].uid}')
#                     print("This is the selected answers {answer_id}")
#                     print("This is the selected question {question}")
#                     if answer_id:
#                         answer = get_object_or_404(Answer, uid=answer_id)
#                         print("This answer would be {answer}")
#                         given_question, created = GivenQuizQuestions.objects.get_or_create(
#                             quiz=quiz, question=question, defaults={
#                                 'answer': answer}
#                         )
#                         print("This is the selected answers {given_question}")

#                         if not created:
#                             given_question.answer = answer
#                             given_question.save()

#                         quiz.given_question.add(given_question)
#                         quiz.save()

#                         print("This is the selected answers {given_question}")

#                     # Move to the next page if available
#                     next_page_number = page_obj.next_page_number() if page_obj.has_next() else None
#                     if next_page_number is not None:
#                         return redirect(f'/quizzes/quizzes/quiz/?page={next_page_number}')
#                     else:
#                         return render(request, 'dashboard/success.html')

#                 quiz.marks = calculate_marks(quiz)
#                 quiz.total_marks = sum(question.mark for question in questions)
#                 quiz.save()

#                 context = {'page_obj': page_obj,
#                            'quiz': quiz, 'quiz_mode': quiz_mode, }
#                 return render(request, 'dashboard/quiz.html', context)

#     else:
#         form = QuizForm(topics_choices=[
#             (topic, topic) for topic in Question.objects.values_list('topic', flat=True).distinct()
#         ])

#     return render(request, 'dashboard/create_question.html', {'form': form})

def quiz_create(request):
    request.session.pop('correct_answer', None)
    request.session.pop('selected_answer', None)
    if request.method == 'POST':
        form = QuizForm(request.POST, topics_choices=sorted(set([
            (topic, topic) for topic in Question.objects.values_list('topic', flat=True).distinct()
        ])))
        if form.is_valid():
            selected_topics = form.cleaned_data['topics']
            question_limit = form.cleaned_data['num_questions']
            quiz_mode = form.cleaned_data['quiz_mode']

            # Check if 'Select All' option is selected
            if QuizForm.ALL_TOPICS_OPTION in selected_topics:
                selected_topics = [
                    topic for topic, _ in form.fields['topics'].choices if topic != QuizForm.ALL_TOPICS_OPTION]

            if selected_topics:
                questions = Question.objects.filter(
                    topic__in=selected_topics
                ).distinct()[:question_limit]

                if not questions.exists():
                    return HttpResponse("No questions found for selected topics.")

                total_marks = sum(question.mark for question in questions)

                exam_mode = True if quiz_mode == "Exam Mode" else False

                quiz = Quiz.objects.create(
                    user=request.user,
                    total_marks=total_marks, marks=0, exam_mode=exam_mode,
                )
                question_ids = [str(q.uid)
                                for q in questions]

                request.session['quiz_id'] = str(quiz.uid)
                request.session['quiz_mode'] = quiz_mode
                request.session['question_ids'] = ','.join(question_ids)

                return redirect('quiz:quiz_start')

    else:
        form = QuizForm(topics_choices=sorted(set([
            (topic, topic) for topic in Question.objects.values_list('topic', flat=True).distinct()
        ])))

    return render(request, 'dashboard/create_question.html', {'form': form})


# def quiz_start(request):
#     quiz_id = request.session.get('quiz_id')
#     print(quiz_id)
#     quiz_mode = request.session.get('quiz_mode')
#     print(quiz_mode)
#     question_ids = request.session.get('question_ids')
#     print(question_ids)
#     # Default to 1 hour if not provided
#     time_left = request.POST.get('time_left', 3600)
#     request.session['time_left'] = time_left

#     if not all([quiz_id, quiz_mode, question_ids]):
#         return redirect('quiz:quiz_create')

#     # Convert question_ids from session data
#     question_ids_list = question_ids.split(',')
#     valid_uuids = []

#     for qid in question_ids_list:
#         try:
#             valid_uuid = uuid.UUID(qid)
#             valid_uuids.append(valid_uuid)
#         except ValueError:
#             continue  # Skip invalid UUIDs

#     if not valid_uuids:
#         return HttpResponse("No valid questions found for this quiz.")

#     # Get the Quiz object
#     quiz = Quiz.objects.get(uid=quiz_id)
#     questions = Question.objects.filter(uid__in=question_ids_list)

#     # Set up pagination
#     paginator = Paginator(questions, 1)  # Show one question per page
#     page_number = request.GET.get('page', 1)

#     try:
#         page_obj = paginator.page(page_number)
#     except PageNotAnInteger:
#         page_obj = paginator.page(1)
#     except EmptyPage:
#         page_obj = paginator.page(paginator.num_pages)

#     if request.method == 'POST':
#         question = page_obj.object_list[0]
#         print(page_obj.object_list[0].uid)
#         answer_id = request.POST.get(f'answer_{question.uid}')
#         print(answer_id)

#         if answer_id:
#             answer = get_object_or_404(Answer, uid=answer_id)
#             print("this is the answer {answer}")
#             given_question, created = GivenQuizQuestions.objects.get_or_create(
#                 quiz=quiz,
#                 question=question, defaults={'answer': answer}
#             )
#             if not created:
#                 given_question.answer = answer
#                 given_question.save()

#             # Update the quiz marks if the answer is correct
#             if answer.is_correct:
#                 quiz.marks += question.mark
#                 quiz.save()

#             quiz.given_question.add(given_question)
#             quiz.save()

#         # Redirect to the next question
#         next_page_number = page_obj.next_page_number() if page_obj.has_next() else None
#         if next_page_number:
#             return redirect(f'/quiz/start/?page={next_page_number}')
#         else:
#             return render(request, 'dashboard/success.html', {'clear_storage': True, 'total_score': quiz.marks, "total_points": quiz.total_marks})

#     context = {
#         'page_obj': page_obj,
#         'quiz': quiz,
#         'quiz_mode': quiz_mode,
#         'question_ids': ','.join(question_ids),
#         'time_left': request.session.get('time_left', 3600),
#     }
#     return render(request, 'dashboard/quiz.html', context)
def quiz_start(request):
    quiz_id = request.session.get('quiz_id')
    print(quiz_id)
    quiz_mode = request.session.get('quiz_mode')
    print(quiz_mode)
    question_ids = request.session.get('question_ids')
    print(question_ids)

    if not all([quiz_id, quiz_mode, question_ids]):
        return redirect('quiz:quiz_create')

    question_ids_list = question_ids.split(',')
    valid_uuids = []

    for qid in question_ids_list:
        try:
            valid_uuid = uuid.UUID(qid)
            valid_uuids.append(valid_uuid)
        except ValueError:
            continue

    if not valid_uuids:
        return HttpResponse("No valid questions found for this quiz.")

    quiz = Quiz.objects.get(uid=quiz_id)
    questions = Question.objects.filter(uid__in=valid_uuids)

    paginator = Paginator(questions, 1)
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    if request.method == 'POST':
        question = page_obj.object_list[0]
        answer_id = request.POST.get(f'answer_{question.uid}')

        if answer_id:
            answer = get_object_or_404(Answer, uid=answer_id)

            given_question, created = GivenQuizQuestions.objects.get_or_create(
                quiz=quiz,
                question=question, defaults={'answer': answer}
            )
            if not created:
                given_question.answer = answer
                given_question.save()

            if answer.is_correct:
                quiz.marks += question.mark
                quiz.save()

            quiz.given_question.add(given_question)
            quiz.save()
            if quiz_mode == "Study Mode":
                request.session['current_question_uid'] = str(question.uid)
                correct_answer = Answer.objects.filter(
                    question=question, is_correct=True).first()
                request.session['correct_answer'] = str(
                    correct_answer.uid) if correct_answer else None

                request.session['answer_acknowledged'] = True

                return render(request, 'dashboard/quiz.html', {
                    'page_obj': page_obj,
                    'quiz': quiz,
                    'quiz_mode': quiz_mode,
                    'question_ids': ','.join(question_ids),
                    'time_left': request.session.get('time_left', 3600),
                    'correct_answer': correct_answer,
                    'selected_answer': answer,
                    'answer_acknowledged': True,
                    'study_mode': quiz_mode == "Study Mode"
                })
            else:
                request.session.pop('selected_answer', None)
                # Redirect to the next question
                next_page_number = page_obj.next_page_number() if page_obj.has_next() else None
                if next_page_number:
                    return redirect(f'/quiz/start/?page={next_page_number}')

        next_page_number = page_obj.next_page_number() if page_obj.has_next() else None
        if next_page_number:
            # Clear previous question session variables
            request.session.pop('current_question_uid', None)
            request.session.pop('correct_answer', None)
            request.session.pop('selected_answer', None)
            request.session.pop('answer_acknowledged', None)

            return redirect(f'/quiz/start/?page={next_page_number}')
        else:
            current_user = request.user
            if not current_user.is_authenticated:
                return redirect('login')

            user_quizzes = Quiz.objects.filter(user=current_user)
            current_user_attempts = user_quizzes.count()
            current_user_total_score = user_quizzes.aggregate(
                total_score=Sum('marks'))['total_score'] or 0

            top_users = User.objects.annotate(
                attempts=Count('quiz'),
                total_score=Sum('quiz__marks')
            ).order_by('-total_score', '-attempts')[:5]

            leaderboard = list(top_users.values(
                'username', 'total_score', 'attempts'))

            current_user_dict = {
                'username': current_user.username,
                'total_score': current_user_total_score,
                'attempts': current_user_attempts,
                'is_current_user': True
            }

            if current_user_dict['username'] not in [user['username'] for user in leaderboard]:
                leaderboard.append(current_user_dict)

            for user in leaderboard:
                user['total_score'] = user.get('total_score', 0) or 0
                user['attempts'] = user.get('attempts', 0) or 0

            leaderboard = sorted(
                leaderboard, key=lambda x: (-x['total_score'], -x['attempts']))

            if len(leaderboard) > 5:
                leaderboard = leaderboard[:5]

            return render(request, 'dashboard/success.html', {
                'leaderboard': leaderboard,
                'current_user': current_user,
                'clear_storage': True,
                'total_score': quiz.marks,
                'total_points': quiz.total_marks
            })

    current_question_uid = request.session.get('current_question_uid')
    correct_answer_uid = request.session.pop('correct_answer', None)
    request.session.pop('selected_answer', None)
    correct_answer = Answer.objects.filter(
        uid=correct_answer_uid).first() if correct_answer_uid else None
    answer_acknowledged = request.session.pop('answer_acknowledged', False)
    selected_answer_uid = None
    if quiz_mode == "Study Mode" and current_question_uid:
        if str(page_obj.object_list[0].uid) != current_question_uid:
            request.session.pop('current_question_uid', None)
            request.session.pop('correct_answer', None)
            request.session.pop('selected_answer', None)
            request.session.pop('answer_acknowledged', None)
        elif answer_acknowledged:
            request.session.pop('selected_answer', None)
            next_page_number = page_obj.next_page_number() if page_obj.has_next() else None
            if next_page_number:
                return redirect(f'/quiz/start/?page={next_page_number}')
            else:
                current_user = request.user
                if not current_user.is_authenticated:
                    return redirect('login')

                user_quizzes = Quiz.objects.filter(user=current_user)
                current_user_attempts = user_quizzes.count()
                current_user_total_score = user_quizzes.aggregate(
                    total_score=Sum('marks'))['total_score'] or 0

                top_users = User.objects.annotate(
                    attempts=Count('quiz'),
                    total_score=Sum('quiz__marks')
                ).order_by('-total_score', '-attempts')[:5]

                leaderboard = list(top_users.values(
                    'username', 'total_score', 'attempts'))

                current_user_dict = {
                    'username': current_user.username,
                    'total_score': current_user_total_score,
                    'attempts': current_user_attempts,
                    'is_current_user': True
                }

                if current_user_dict['username'] not in [user['username'] for user in leaderboard]:
                    leaderboard.append(current_user_dict)

                for user in leaderboard:
                    user['total_score'] = user.get('total_score', 0) or 0
                    user['attempts'] = user.get('attempts', 0) or 0

                leaderboard = sorted(
                    leaderboard, key=lambda x: (-x['total_score'], -x['attempts']))

                if len(leaderboard) > 5:
                    leaderboard = leaderboard[:5]

                return render(request, 'dashboard/success.html', {
                    'leaderboard': leaderboard,
                    'current_user': current_user,
                    'clear_storage': True,
                    'total_score': quiz.marks,
                    'total_points': quiz.total_marks
                })

    context = {
        'page_obj': page_obj,
        'quiz': quiz,
        'quiz_mode': quiz_mode,
        'question_ids': ','.join(question_ids),
        'time_left': request.session.get('time_left', 3600),
        'correct_answer': correct_answer,
        'answered_question': current_question_uid,
        'answer_acknowledged': answer_acknowledged,
        'selected_answer_uid': selected_answer_uid,
        'study_mode': quiz_mode == "Study Mode"
    }

    return render(request, 'dashboard/quiz.html', context)


def readiness_quiz_start(request):
    request.session.pop('correct_answer', None)
    request.session.pop('selected_answer', None)
    if request.method == 'POST':
        # Creating the quiz and shuffling questions
        questions = Question.objects.all()

        if not questions.exists():
            return HttpResponse("No questions available.")

        # Shuffle questions
        questions = list(questions)
        random.shuffle(questions)

        # Creating a quiz
        try:
            quiz = Quiz.objects.create(
                user=request.user,
                exam_mode=False,
                total_marks=sum(question.mark for question in questions),
                marks=0,  # Starting marks
            )
        except Exception as e:
            return HttpResponse(f"Error creating quiz: {e}")

        question_ids = [str(q.uid) for q in questions]

        request.session['quiz_id'] = str(quiz.uid)
        request.session['quiz_mode'] = "Study Mode"
        request.session['question_ids'] = ','.join(question_ids)

        # Redirect to the same view to display the quiz
        return redirect('quiz:quiz_start')
    else:
        # Handling the initial load or quiz display
        quiz_id = request.session.get('quiz_id')
        question_ids = request.session.get('question_ids')

        if not all([quiz_id, question_ids]):
            return HttpResponse("No quiz session found. Please start a new quiz.")

        # Convert question_ids from session data
        question_ids_list = question_ids.split(',')
        valid_uuids = []

        for qid in question_ids_list:
            try:
                valid_uuid = uuid.UUID(qid)
                valid_uuids.append(valid_uuid)
            except ValueError:
                continue  # Skip invalid UUIDs

        if not valid_uuids:
            return HttpResponse("No valid questions found for this quiz.")

        # Get the Quiz object
        try:
            quiz = Quiz.objects.get(uid=quiz_id)
        except Quiz.DoesNotExist:
            return HttpResponse("Quiz not found.")

        questions = Question.objects.filter(uid__in=question_ids_list)

        # Set up pagination
        paginator = Paginator(questions, 1)  # Show one question per page
        page_number = request.GET.get('page', 1)

        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        if request.method == 'POST':
            question = page_obj.object_list[0]
            answer_id = request.POST.get(f'answer_{question.uid}')

            if answer_id:
                try:
                    answer = get_object_or_404(Answer, uid=answer_id)
                except Answer.DoesNotExist:
                    return HttpResponse("Answer not found.")

                # Update the quiz marks if the answer is correct
                if answer.is_correct:
                    quiz.marks += question.mark
                    quiz.save()

            # Redirect to the next question
            next_page_number = page_obj.next_page_number() if page_obj.has_next() else None
            if next_page_number:
                return redirect(f'/quiz/view/?page={next_page_number}')
            else:

                current_user = request.user

                # Ensure user is logged in
                if not current_user.is_authenticated:
                    return redirect('login')

                # Retrieve all quizzes associated with the current user
                user_quizzes = Quiz.objects.filter(user=current_user)

                # Calculate total score and attempts
                current_user_attempts = user_quizzes.count()
                current_user_total_score = user_quizzes.aggregate(
                    total_score=Sum('marks'))['total_score'] or 0

                # Retrieve the top 5 users based on total quiz attempts and scores
                top_users = User.objects.annotate(
                    attempts=Count('quiz'),
                    total_score=Sum('quiz__marks')
                ).order_by('-total_score', '-attempts')[:5]

                # Prepare leaderboard and include current user
                leaderboard = list(top_users.values(
                    'username', 'total_score', 'attempts'))

                current_user_dict = {
                    'username': current_user.username,
                    'total_score': current_user_total_score,
                    'attempts': current_user_attempts,
                    'is_current_user': True
                }

                # Check if current user is already in the top_users
                if current_user_dict['username'] not in [user['username'] for user in leaderboard]:
                    # Add current user to leaderboard
                    leaderboard.append(current_user_dict)

                # Handle None values by replacing them with default values
                for user in leaderboard:
                    user['total_score'] = user.get('total_score', 0) or 0
                    user['attempts'] = user.get('attempts', 0) or 0

                # Sort leaderboard to ensure correct order
                leaderboard = sorted(
                    leaderboard, key=lambda x: (-x['total_score'], -x['attempts']))

                # Ensure leaderboard shows only top 5 users and the current user if they are not in the top 5
                if len(leaderboard) > 5:
                    leaderboard = leaderboard[:5]

                # Render success page with leaderboard
                return render(request, 'dashboard/success.html', {
                    'leaderboard': leaderboard,
                    'current_user': current_user,
                    'clear_storage': True,
                    'total_score': quiz.marks,
                    'total_points': quiz.total_marks
                })

        context = {
            'page_obj': page_obj,
            'quiz': quiz,
            'question_ids': ','.join(question_ids),
        }
        return render(request, 'dashboard/quiz.html', context)


@login_required
def retake_quiz(request):
    quiz_id = request.GET.get('quiz_id')
    original_quiz = get_object_or_404(Quiz, uid=quiz_id, user=request.user)

    # Create a new quiz instance
    new_quiz = Quiz.objects.create(
        user=request.user,
        total_marks=original_quiz.total_marks,
        marks=0,
        exam_mode=original_quiz.exam_mode,
    )

    # Copy questions from the original quiz
    for given_question in original_quiz.given_question.all():
        new_given_question = GivenQuizQuestions.objects.create(
            question=given_question.question,
            quiz=new_quiz
        )

        # Add the new given question to the quiz
        new_quiz.given_question.add(new_given_question)

    new_quiz.save()

    request.session['quiz_id'] = str(new_quiz.uid)
    request.session['quiz_mode'] = "Study Mode" if new_quiz.exam_mode == False else "Exam Mode"
    question_ids = [str(gq.question.uid)
                    for gq in new_quiz.given_question.all()]
    request.session['question_ids'] = ','.join(question_ids)

    return redirect('quiz:quiz_start')


def success_screen(request):

    return render(request, 'dashboard/success.html')


def sign_in(request):
    return render(request, 'signin.html')


def logout_view(request):
    logout(request)
    return redirect('/')


@login_required
def loadAttendedQuestionData(request, uid):
    context = {}
    try:
        # Get the user's quiz where the given question matches the provided uid
        givenQuiz = Quiz.objects.filter(
            Q(user=request.user) & Q(given_question__question__uid=uid)
        ).distinct()

        is_question_attended = givenQuiz.exists()
        payload = []
        context['status'] = 404

        if is_question_attended:
            context['status'] = 200
            quiz = givenQuiz.first()
            all_given_questions = quiz.given_question.filter(question__uid=uid)
            given_question = all_given_questions.first()
            given_answer = given_question.answer

            for answer in given_question.question.answers.all():
                payload.append({
                    'uid': str(answer.uid),
                    'isCorrect': str(answer.is_correct),
                    'isSelected': 'true' if answer == given_answer else 'false'
                })

        context['payload'] = payload

    except Exception as e:
        print(e)  # Optional: log the exception for debugging purposes
        context['status'] = 404

    return JsonResponse(context)


@login_required
def myprofile(request):
    try:
        profile = request.user
    except profile.DoesNotExist:
        profile = None

    if request.method == 'POST':
        profile_form = ProfileUpdateForm(request.POST, user=request.user)
        if profile_form.is_valid():
            profile_form.save()
            # profile.user = request.user
            # profile.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('myprofile')
    else:
        profile_form = ProfileUpdateForm(user=request.user)

    context = {'profile_form': profile_form}
    return render(request, 'dashboard/myprofile.html', context)


@login_required
def quizAttempts(request):
    user = request.user
    courses = StudyCategoryModel.objects.all()

    context = {
        'data_context': courses,
    }
    return render(request, 'dashboard/quiz_attempts.html', context)


def study_detail(request):
    id = request.GET.get('id')
    print(f"Received ID: {id}")

    topic = get_object_or_404(StudyTopicModel, uid=id)
    try:
        post = StudyModel.objects.get(topic=topic)
    except StudyModel.DoesNotExist:
        return render(request, '404.html',)
    context = {
        'post': post,
    }
    return render(request, 'dashboard/course_detail.html', context)


@login_required
def study_topics(request):
    category_id = request.GET.get('id')
    if category_id is None:
        return render(request, 'error.html', {'error': 'No category ID provided.'})
    category = get_object_or_404(StudyCategoryModel, uid=category_id)
    topics = StudyTopicModel.objects.filter(category=category)

    context = {
        'data_context': topics,
    }
    return render(request, 'dashboard/study_topics.html', context)


@login_required
def subscription(request):
    return render(request, 'dashboard/subscription.html',)


@login_required
def creat_subscription(request, days):
    # Example subscription period: 1 month
    end_date = timezone.now() + timedelta(days=days)
    subscription, created = UserSubscription.objects.get_or_create(
        user=request.user,
        defaults={'subscription_end_date': end_date}
    )
    if not created:
        # Update subscription end date if it already exists
        subscription.subscription_end_date = end_date
        subscription.save()
    return render(request, 'dashboard/index.html',)


@login_required
def settings(request):
    return render(request, 'dashboard/settings.html',)


@login_required
def enrolled_courses(request):
    user = request.user
    quizzes = Quiz.objects.filter(
        user=user, given_question__isnull=False).distinct().order_by('-created_at')
    context = {
        'quizzes': quizzes,
    }
    return render(request, 'dashboard/enrolled_courses.html', context)


@login_required
def quiz_questions(request):
    quiz_id = request.GET.get('quiz_id')
    quiz = get_object_or_404(Quiz, uid=quiz_id, user=request.user)
    given_questions = quiz.given_question.all()
    questions = [
        {
            'question': gq.question,
            'selected_answer': gq.answer,
            'answers': gq.question.answers.all()
        }
        for gq in given_questions
    ]
    context = {
        'quiz': quiz,
        'questions': questions,
    }
    print(context)  # Debug statement
    return render(request, 'dashboard/quiz_questions.html', context)


@login_required
def start_quiz(request):
    category = request.GET.get('category')
    user = request.user
    topic = get_object_or_404(StudyTopicModel, uid=category)
    quiz_query = Quiz.objects.filter(Q(user=user) & Q(topic=topic))

    if not quiz_query.exists():
        quiz = Quiz.objects.create(
            user=user, total_marks=0, topic=topic, marks=0
        )
    else:
        quiz = quiz_query.first()

    return redirect(f'quiz/?category={category}')


@login_required
def quizzes(request):
    categories = Category.objects.all()
    context = {'categories': categories, 'homeactive': True}

    category_text = request.GET.get('category')
    if category_text:
        user = request.user
        category = Category.objects.get(name=category_text)
        topics = StudyTopicModel.objects.filter(category=category)

        context = {
            'data_context': topics,
        }
        return render(request, 'dashboard/quiz_topics.html', context)

    return render(request, 'dashboard/quizzes.html', context)


def study_list(request):
    study = StudyModel.objects.all()
    return render(request, 'dashboard/enrolled_courses.html', {'context': study})


@login_required
def help(request):
    return render(request, 'dashboard/help.html',)


def text_analitics(request):
    return render(request, 'dashboard/text_analitics.html')

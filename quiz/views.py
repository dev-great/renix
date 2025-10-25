import random
from django.shortcuts import get_object_or_404, render, HttpResponse, redirect
from django.urls import reverse
from quiz.forms import ProfileUpdateForm, QuizForm
from django.db.models import Count, Sum
from . models import *
from django.http import Http404, JsonResponse
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


def quiz_create(request):
    request.session.pop('correct_answer', None)
    request.session.pop('selected_answer', None)

    if request.method == 'POST':
        user_subscription = UserSubscription.objects.filter(
            user=request.user).first()
        topics_choices = []

        if user_subscription:
            topics_choices = sorted(
                (topic.title, topic.title)
                for topic in StudyTopicModel.objects.filter(plan__name=user_subscription.plan)
            )

        form = QuizForm(request.POST, topics_choices=topics_choices)

        if form.is_valid():
            selected_topics = form.cleaned_data['topics']
            question_limit = form.cleaned_data['num_questions']
            quiz_mode = form.cleaned_data['quiz_mode']

            print(selected_topics)
            # Check if 'Select All' option is selected
            if QuizForm.ALL_TOPICS_OPTION in selected_topics:
                selected_topics = [
                    topic for topic, _ in form.fields['topics'].choices if topic != QuizForm.ALL_TOPICS_OPTION]

            # Get total unanswered questions for selected topics
            total_unanswered = 0
            for topic_title in selected_topics:
                total_questions = Question.objects.filter(category__title=topic_title).count()
                user_quizzes = Quiz.objects.filter(user=request.user)
                answered_questions = GivenQuizQuestions.objects.filter(
                    quiz__in=user_quizzes,
                    question__category__title=topic_title
                ).values_list('question', flat=True).distinct()

                unanswered_questions_count = total_questions - answered_questions.count()
                total_unanswered += unanswered_questions_count

            # 🔍 Validation: check if the user selected more than available unanswered questions
            if question_limit > total_unanswered:
                messages.error(
                    request,
                    f"You selected {question_limit} questions, but only {total_unanswered} unanswered questions are available."
                )
                return redirect('quiz:quiz_create')

            # Continue as before if validation passes
            questions = Question.objects.filter(
                isReadiness=False,
                category__title__in=selected_topics
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
        user_subscription = UserSubscription.objects.filter(user=request.user).first()
        topics_choices = []

        if user_subscription:
            topics_with_counts = []

            # Get topics based on user's subscription plan
            topics = StudyTopicModel.objects.filter(plan__name=user_subscription.plan)

            for topic in topics:
                # Get total number of questions for this topic
                total_questions = Question.objects.filter(category__title=topic.title).count()

                # Get all quizzes the user has taken
                user_quizzes = Quiz.objects.filter(user=request.user)

                # Get all answered questions for the topic by the user
                answered_questions = GivenQuizQuestions.objects.filter(
                    quiz__in=user_quizzes,
                    question__category__title=topic.title
                ).values_list('question', flat=True).distinct()

                # Calculate unanswered questions
                unanswered_questions_count = total_questions - answered_questions.count()

                # Only include topics that have unanswered questions
                if unanswered_questions_count >= 0:
                    topics_with_counts.append((topic.title, f'{topic.title} ({unanswered_questions_count}/{unanswered_questions_count})'))

            topics_choices = sorted(topics_with_counts)

        form = QuizForm(topics_choices=topics_choices)

    return render(request, 'dashboard/create_question.html', {'form': form,'current_plan': user_subscription.plan if user_subscription else None})


def quiz_start(request):
    quiz_id = request.session.get('quiz_id')
    print(quiz_id)
    quiz_mode = request.session.get('quiz_mode')
    print(quiz_mode)
    question_ids = request.session.get('question_ids')
    print(question_ids)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    user_subscription = UserSubscription.objects.filter(user=request.user).first()

    # --- Handle missing quiz session data ---
    if not all([quiz_id, quiz_mode, question_ids]):
        return redirect('quiz:quiz_create')

    # --- Convert question IDs to valid UUIDs ---
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

    # --- Handle first-time users ---
    if not GivenQuizQuestions.objects.filter(quiz__user=request.user).exists():
        # You can customize this to show a welcome modal or onboarding page
        request.session['first_time_user'] = True
    else:
        request.session['first_time_user'] = False

    # --- Pagination setup ---
    paginator = Paginator(questions, 1)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # --- Handle form submissions ---
    if request.method == 'POST':
        # Stop quiz early
        if 'stop_button' in request.POST:
            return redirect('success_page')

        question = page_obj.object_list[0]
        answer_id = request.POST.get(f'answer_{question.uid}')

        if answer_id:
            answer = get_object_or_404(Answer, uid=answer_id)

            # Record or update given question
            given_question, created = GivenQuizQuestions.objects.get_or_create(
                quiz=quiz,
                question=question,
                defaults={'answer': answer}
            )
            if not created:
                given_question.answer = answer
                given_question.save()

            # Update quiz marks
            if answer.is_correct:
                quiz.marks += question.mark
                quiz.save()

            quiz.given_question.add(given_question)
            quiz.save()

            # --- Study Mode Handling ---
            if quiz_mode == "Study Mode":
                request.session['current_question_uid'] = str(question.uid)
                correct_answer = Answer.objects.filter(
                    question=question, is_correct=True).first()
                request.session['correct_answer'] = str(
                    correct_answer.uid) if correct_answer else None

                request.session['answer_acknowledged'] = True

                print(f"Subscription plan {{user_subscription.plan}}")

                plan_name = user_subscription.plan if user_subscription else "Free Plan"

                if plan_name == 'College/Sch. of Nursing Entrance':
                    time_left = request.session.get('time_left', 7200)
                else:
                    time_left = request.session.get('time_left', 10800)

                return render(request, 'dashboard/quiz.html', {
                    'page_obj': page_obj,
                    'quiz': quiz,
                    'quiz_mode': quiz_mode,
                    'current_plan': user_subscription.plan if user_subscription else "Free Plan",
                    'question_ids': ','.join(question_ids),
                    'time_left': time_left,
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
        'current_plan': user_subscription.plan if user_subscription else "Free Plan",
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
    user_subscription = UserSubscription.objects.filter(
        user=request.user).first()

    print(user_subscription)
    questions = []

    if user_subscription:
        plan_name = user_subscription.plan
        topics = StudyTopicModel.objects.filter(plan__name=plan_name)

        # Extract the titles of the topics
        topic_titles = topics.values_list('title', flat=True)
        if plan_name == "College/Sch. of Nursing Entrance":
            questions = Question.objects.filter(isReadiness=True,category__title__in=topic_titles).order_by('?')[:100]
        else:
            questions = Question.objects.filter(isReadiness=True,category__title__in=topic_titles).order_by('?')[:250]

        print(topics)
        print(questions)
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

    print(question_ids)

    request.session['quiz_id'] = str(quiz.uid)
    request.session['quiz_mode'] = "Readiness"
    request.session['question_ids'] = ','.join(question_ids)

    # Redirect to the same view to display the quiz
    return redirect('quiz:quiz_start')


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
    request.session.pop('quiz_id', None)
    request.session.pop('quiz_mode', None)
    request.session.pop('question_ids', None)
    request.session.pop('current_question_uid', None)
    request.session.pop('correct_answer', None)
    request.session.pop('selected_answer', None)
    request.session.pop('answer_acknowledged', None)

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
    user = request.user

    # Check if the user already has a profile
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        profile_form = ProfileUpdateForm(request.POST, user=user, instance=profile)

        if profile_form.is_valid():
            profile_form.save()

            user.first_name = profile_form.cleaned_data['first_name']
            user.last_name = profile_form.cleaned_data['last_name']
            user.email = profile_form.cleaned_data['email']
            user.save()

            profile.school_name = profile_form.cleaned_data['school_name']
            profile.save()

            messages.success(request, 'Your profile has been updated!')
            return redirect('quiz:myprofile')
    else:
        profile_form = ProfileUpdateForm(user=user, instance=profile)

    context = {'profile_form': profile_form}
    return render(request, 'dashboard/myprofile.html', context)


@login_required
def quizAttempts(request):
    user_subscription = UserSubscription.objects.filter(
        user=request.user).first()
    if user_subscription:
        plan_name = user_subscription.plan
        courses = StudyCategoryModel.objects.filter(
            plan_group__name=plan_name).order_by('-created_at')

    context = {
        'data_context': courses,
    }
    return render(request, 'dashboard/quiz_attempts.html', context)


@login_required
def quizTopics(request):
    category_text = request.GET.get('category')
    user_subscription = UserSubscription.objects.filter(
        user=request.user).first()
    if user_subscription:
        result = StudyModel.objects.filter(category__name=category_text)
    else:
        result = []

    print(result)

    context = {
        'data_context': result,
    }
    return render(request, 'dashboard/quiz_topics.html', context)


def study_detail(request):
    id = request.GET.get('id')
    print(f"Received ID: {id}")

    post = StudyModel.objects.filter(uid=id).first()
    if not post:
        return render(request, '404.html')

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
    topic = StudyTopicModel.objects.filter(category=category).first()
    result = StudyModel.objects.filter(topic=topic)

    context = {
        'data_context': result,
    }
    return render(request, 'dashboard/study_topics.html', context)


@login_required
def subscription(request):

    user_subscription = UserSubscription.objects.filter(
        user=request.user, is_active=True).first()

    context = {
        'data_context': user_subscription,
        'current_plan': user_subscription.plan if user_subscription else None
    }
    return render(request, 'dashboard/subscription.html', context)

@login_required
def subscription_success(request):
    
    return render(request, 'dashboard/subscription_success.html',)


@login_required
def create_subscription(request, days, plan):
    # Example subscription period: 1 month
    end_date = timezone.now() + timedelta(days=int(days))
    plan = plan.replace("_", " ")

    try:
        # Check if the user already has a subscription
        subscription = UserSubscription.objects.filter(
            user=request.user).first()

        # If a subscription exists and the plans do not match, delete the old subscription
        if subscription and subscription.plan != plan:
            subscription.delete()
            subscription = None  # We'll create a new one below

        # If no subscription exists or it was deleted, create a new one
        if not subscription:
            subscription = UserSubscription.objects.create(
                user=request.user,
                plan=plan,
                subscription_end_date=end_date
            )
        else:
            # Update the existing subscription if the plans match
            subscription.subscription_end_date = end_date
            subscription.save()

        # Mark the user as having an active subscription
        request.has_active_subscription = True

    except Exception as e:
        print(e)
        return render(request, 'dashboard/error.html', {'error': str(e)})

    return render(request, 'dashboard/subscription_success.html')


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
    # request.session.flush()
    # request.session.pop('quiz_id', None)
    # request.session.pop('quiz_mode', None)
    # request.session.pop('question_ids', None)
    # request.session.pop('current_question_uid', None)
    # request.session.pop('correct_answer', None)
    # request.session.pop('answer_acknowledged', None)
    # request.session.pop('selected_answer', None)

    user_subscription = UserSubscription.objects.filter(
        user=request.user).first()
    context = {'context': user_subscription, 'homeactive': True}

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

def practice(request):
    return render(request, 'dashboard/practice_test.html')


def trial_study_mode(request):
    user = request.user
    existing_quiz = Quiz.objects.filter(user=user, exam_mode=False).first()
    all_questions = list(Question.objects.all())

    # Ensure the user is authenticated
    if not user.is_authenticated:
        return render(request, "dashboard/message.html", {
            "title": "Login Required",
            "message": "Please log in to take your free trial quiz.",
            "button_text": "Login Now",
            "button_url": reverse("login")
        })

    if existing_quiz:
        return render(request, "dashboard/message.html", {
            "title": "Trial Quiz Already Taken",
            "message": "You’ve already used your free trial. Subscribe to unlock more quizzes.",
            "button_text": "Back to Dashboard",
            "button_url": "subscription/"
        })

    if len(all_questions) < 50:
        return render(request, "dashboard/message.html", {
            "title": "Not Enough Questions",
            "message": "We’re preparing more questions. Please check back later!",
            "button_text": "Back to Dashboard",
            "button_url": reverse("dashboard")
        })

    questions = random.sample(all_questions, 50)

    # ✅ Create quiz in study mode
    try:
        quiz = Quiz.objects.create(
            user=user,
            exam_mode=False,  # Study mode
            total_marks=sum(q.mark for q in questions),
            marks=0,  # Starting mark
        )
    except Exception as e:
        return HttpResponse(f"Error creating quiz: {e}")

    # Store question UIDs in session
    question_ids = [str(q.uid) for q in questions]
    request.session['quiz_id'] = str(quiz.uid)
    request.session['quiz_mode'] = "Study Mode"
    request.session['question_ids'] = ','.join(question_ids)

    # ✅ Redirect to the quiz start page
    return redirect('quiz:quiz_start')
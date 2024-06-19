from django.shortcuts import get_object_or_404, render, HttpResponse, redirect

from quiz.forms import ProfileUpdateForm
from . models import *
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q


# Create your views here.

@login_required
def index(request):
    user = request.user

    # List of attempted quizzes
    attempted_quizzes = Quiz.objects.filter(
        user=user, given_question__isnull=False).distinct().order_by('-end_time')[:5]

    # Top 5 activities
    last_login_time = User.objects.filter(
        pk=request.user.pk).values_list('last_login', flat=True).first()

    # Get the latest course in Quiz
    latest_course = Quiz.objects.filter(
        user=request.user).order_by('-end_time').first()

    # Get the latest Category added
    latest_category = Category.objects.order_by('-created_at').first()

    # Number of courses, enrolled courses, and completed courses
    total_courses = Category.objects.count()
    enrolled_courses = Quiz.objects.filter(user=user).count()
    completed_courses = Quiz.objects.filter(
        user=user, end_time__isnull=False).count()

    context = {
        'attempted_quizzes': attempted_quizzes,
        'last_login_time': last_login_time,
        'latest_course': latest_course,
        'latest_category': latest_category,
        'total_courses': total_courses,
        'enrolled_courses': enrolled_courses,
        'completed_courses': completed_courses,
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
                user=request.user, category=answer.question.category)
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
    marks = 0
    for given_question in quiz.given_question.all():
        if given_question.answer.is_correct:
            marks += given_question.question.mark
    return marks


def quiz(request):
    category = request.GET.get('category')
    if category:
        quiz, created = Quiz.objects.get_or_create(
            user=request.user, category__name=category)

        questions = Question.objects.filter(category__name=category)
        paginator = Paginator(questions, 1)
        page_number = request.GET.get('page')

        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        if request.method == 'POST':
            answer_uid = request.POST.get(
                f'answer_{page_obj.object_list[0].uid}')
            if answer_uid:
                answer = get_object_or_404(Answer, uid=answer_uid)
                question = get_object_or_404(
                    Question, uid=page_obj.object_list[0].uid)

                given_question, created = GivenQuizQuestions.objects.get_or_create(
                    quiz=quiz, question=question, answer=answer)
                quiz.given_question.add(given_question)
                quiz.save()

                # Move to the next page if available
                next_page_number = page_obj.next_page_number() if page_obj.has_next() else None
                if next_page_number is not None:
                    return redirect(f'/quizzes/quizzes/quiz/?page={next_page_number}&category={category}')
                else:
                    return render(request, 'dashboard/success.html')

        # Calculate marks before rendering the page
        quiz.marks = calculate_marks(quiz)
        quiz.total_marks = sum(question.mark for question in questions)
        quiz.save()

        context = {'page_obj': page_obj, 'category': category, 'quiz': quiz}
        return render(request, 'dashboard/quiz.html', context)

    return redirect('home')


def success_screen(request):
    return render(request, 'dashboard/success_screen.html')


def sign_up(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password1')

        if not username or not email or not password:
            messages.error(request, 'All fields are required.')
            return render(request, 'signup.html', {'sign_up_active': True})

        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username, email=email, password=password)
            user.save()
            messages.success(request, 'Signed up successfully.')
            return redirect('sign_in')

        messages.error(
            request, 'User already exists. Try with a different username.')

    return render(request, 'signup.html', {'sign_up_active': True})


def sign_in(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if (user):
            login(request, user)
            messages.success(request, 'Signined Successfully.')
            return redirect('index')
        messages.error(request, 'Enter valid username or password.')
    return render(request, 'signin.html', {'sign_in_active': True})


def sign_out(request):
    logout(request)
    return redirect('/')


def loadAttendedQuestionData(request, uid):
    context = {}
    try:
        givenQuiz = Quiz.objects.filter(
            Q(user=request.user) & Q(given_question__question__uid=uid)
        )
        is_question_attened = givenQuiz.exists()

        payload = []
        context['status'] = 404
        if is_question_attened:
            context['status'] = 200
            quiz = givenQuiz[0]
            all_given_questions = quiz.given_question.all()
            all_given_questions = all_given_questions.filter(question__uid=uid)
            given_answer = all_given_questions.first().answer
            for i in all_given_questions.first().question.answers.all():
                if i == given_answer:
                    payload.append({'uid': str(i.uid), 'isCorrect': str(
                        i.is_correct), 'isSelected': 'true'})
                else:
                    payload.append({'uid': str(i.uid), 'isCorrect': str(
                        i.is_correct), 'isSelected': 'false'})
        context['payload'] = payload

    except:
        context['status'] = 404
    return JsonResponse(context)


@login_required
def myprofile(request):
    if request.method == 'POST':
        profile_form = ProfileUpdateForm(request.POST, user=request.user)
        if profile_form.is_valid():
            user = request.user
            user.full_name = profile_form.cleaned_data['full_name']
            user.email = profile_form.cleaned_data['email']
            user.save()

            profile = Profile.objects.get(user=user)
            profile.gender = profile_form.cleaned_data['gender']
            profile.address = profile_form.cleaned_data['address']
            profile.save()

            return redirect('myprofile')
    else:
        profile_form = ProfileUpdateForm(user=request.user)

    return render(request, 'dashboard/myprofile.html', {'profile_form': profile_form})


@login_required
def quizAttempts(request):
    user = request.user
    quizzes = Quiz.objects.filter(
        user=user, given_question__isnull=False).distinct()

    for quiz in quizzes:
        if quiz.category.total_marks / 1.5 >= quiz.marks:
            quiz.status = 'yes'  # Successful
        else:
            quiz.status = 'no'  # Failed
        quiz.save()

    context = {
        'quizzes': quizzes,
    }
    return render(request, 'dashboard/quiz_attempts.html', context)


@login_required
def subscription(request):
    return render(request, 'dashboard/subscription.html',)


@login_required
def settings(request):
    return render(request, 'dashboard/settings.html',)


@login_required
def enrolled_courses(request):
    user = request.user
    quizzes = Quiz.objects.filter(
        user=user, given_question__isnull=False).distinct()
    context = {
        'quizzes': quizzes,
    }
    return render(request, 'dashboard/enrolled_courses.html', context)


@login_required
def quiz_questions(request, quiz_id):
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
def quizzes(request):
    categories = Category.objects.all()
    context = {'categories': categories, 'homeactive': True}
    category_text = request.GET.get('category')
    if category_text:
        user = request.user
        quiz_query = Quiz.objects.filter(
            Q(user=user) & Q(category__name=category_text)
        )
        if not quiz_query.exists():
            category = Category.objects.get(name=category_text)

            quiz = Quiz.objects.create(
                user=user, total_marks=0, category=category, marks=0)
            quiz.save()
        else:
            quiz = quiz_query.first()
        return redirect(f'quizzes/quiz/?category={category_text}')
    return render(request, 'dashboard/quizzes.html', context)

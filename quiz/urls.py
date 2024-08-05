# renix/urls.py
from django.urls import path, register_converter
from . import views
from uuid import UUID


class UUIDConverter:
    regex = '[0-9a-f]{32}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{12}'

    def to_python(self, value):
        return UUID(value)

    def to_url(self, value):
        return str(value)


register_converter(UUIDConverter, 'uuid')

app_name = 'quiz'
urlpatterns = [
    path('', views.index, name='index'),
    path('checkAnswer/<uid>/<str:createObj>',
         views.check_answer, name='check_answer'),

    path('quiz/readiness/', views.readiness_quiz_start, name='quiz_readiness'),
    path('quiz/create/', views.quiz_create, name='quiz_create'),
    path('quiz/start/', views.quiz_start, name='quiz_start'),
    path('quiz/retake/', views.retake_quiz, name='retake_quiz'),
    path('create-subscription/<int:days>/',
         views.creat_subscription, name='create_subscription'),

    path('signIn/', views.sign_in, name='sign_in'),
    path('signOut/', views.logout_view, name='sign_out'),
    path('loadAttendedQuestionData/<uid>', views.loadAttendedQuestionData,
         name='load_attended_question_data'),
    path('myprofile/', views.myprofile, name='myprofile'),
    path('quiz_attempts/', views.quizAttempts, name='quiz_attempts'),
    path('quizzes/', views.quizzes, name='quizzes'),
    path('subscription/', views.subscription, name='subscription'),
    path('settings/', views.settings, name='settings'),
    path('enrolled_courses/', views.enrolled_courses, name='enrolled_courses'),
    path('success_screen/', views.success_screen, name='success_screen'),
    path('quiz/questions/',
         views.quiz_questions, name='quiz_questions'),
    path('course/', views.study_detail, name='study_detail'),
    path('topics/', views.study_topics, name='study_topics'),
    path('quiz_detail/', views.start_quiz, name='quiz_detail'),
    path('help/', views.help, name='help'),
    path('text_analitics', views.text_analitics, name='text_analitics')
]

from django.contrib import admin
from . models import *


class AnswerAdmin(admin.StackedInline):
    model = Answer


class QuestionAdmin(admin.ModelAdmin):
    inlines = (AnswerAdmin,)


class StudyModelAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title', 'content')
    list_filter = ('title',)


admin.site.register(StudyModel, StudyModelAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(
    (Category, Answer, Quiz, GivenQuizQuestions, StudyTopicModel, StudyCategoryModel,))

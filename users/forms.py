from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import Permission
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField
from .models import RSUser
from .validators import validate_phone, validate_code


class LoginForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={"autofocus": True, 'placeholder': '05xxxxxxxx'}),
                             label="رقم الجوال", validators=[validate_phone])
    password = forms.CharField(widget=forms.PasswordInput(), label="كلمة المرور")


class CustomerCreateForm(ModelForm):
    phone = forms.CharField(validators=[validate_phone], widget=forms.TextInput(attrs={'placeholder': '05xxxxxxxx'}),
                            label='رقم الجوال')

    class Meta:
        model = RSUser
        fields = ('phone', 'full_name', 'gender')
        labels = {
            'full_name': 'الاسم الكامل',
            'gender': 'الجنس'
        }


class StaffCreateForm(UserCreationForm):
    phone = forms.CharField(validators=[validate_phone], widget=forms.TextInput(attrs={'placeholder': '05xxxxxxxx'}),
                            label='رقم الجوال')

    class Meta:
        model = RSUser
        fields = ('full_name', 'phone', 'gender', 'password1', 'password2')
        labels = {
            'full_name': 'الاسم الكامل',
            # 'email': 'البريد الإلكتروني',
            'gender': 'الجنس',
            # 'profile_picture': 'الصورة الشخصية',
            'password1': 'كلمة المرور',
            'password2': 'تأكيد كلمة المرور'
        }


class StaffUpdateForm(ModelForm):

    class Meta:
        model = RSUser
        fields = ('full_name', 'phone')
        labels = {
            'full_name': 'الاسم الكامل',
            'phone': 'رقم الجوال'
        }


class StaffPermissionsForm(ModelForm):
    reservations_permissions = ['add_reservation', 'add_facility', 'add_timeslot', 'create_report', 'change_price']
    subscriptions_permissions = ['add_division', 'add_subscription', 'view_subscription', 'add_trainingsessionrecord', 'change_subs_price',
                                 'add_trainingweekday']

    reservations_permissions_field = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.filter(codename__in=reservations_permissions),
        widget=forms.CheckboxSelectMultiple,
        label='صلاحيات الحجوزات',
        required=False
    )

    subscriptions_permissions_field = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.filter(codename__in=subscriptions_permissions),
        widget=forms.CheckboxSelectMultiple,
        label='صلاحيات الاشتراكات',
        required=False
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.get('instance')
        super().__init__(*args, **kwargs)

        self.fields['reservations_permissions_field'].initial = user.user_permissions.filter(codename__in=self.reservations_permissions)
        self.fields['subscriptions_permissions_field'].initial = user.user_permissions.filter(codename__in=self.subscriptions_permissions)

    class Meta:
        model = RSUser
        fields = ('is_superuser', 'reservations_permissions_field', 'subscriptions_permissions_field')
        labels = {'is_superuser': 'مدير النظام'}
        help_texts = {'is_superuser': 'يمكن لمدير النظام الوصول إلى كافة الصلاحيات وإنشاء المستخدمين وتغيير صلاحياتهم'}


class CustomerInfoPublicForm(forms.ModelForm):
    phone = forms.CharField(required=True, label='رقم الهاتف', validators=[validate_phone],
                            widget=forms.TextInput(attrs={'placeholder': '05xxxxxxxx'}))
    birth_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}), label='تاريخ الميلاد')

    class Meta:
        model = RSUser
        fields = 'full_name', 'phone', 'gender', 'birth_date'
        labels = {
            'full_name': 'الاسم الكامل',
            'gender': 'الجنس',
        }


class CustomerConfirmationForm(forms.Form):
    confirm_button = forms.BooleanField(widget=forms.HiddenInput(attrs={'value': 'True'}), required=False)


class PhoneForm(forms.Form):
    phone = forms.CharField(validators=[validate_phone], widget=forms.TextInput(attrs={'placeholder': '05xxxxxxxx'}),
                            label='رقم الجوال')

    class Meta:
        fields = ('phone',)
        help_texts = {'phone': 'أدخل رقم الجوال وسيتم إرسال رمز التحقق إليه عبر الواتساب'}


class CodeForm(forms.Form):
    phone = forms.CharField(label='رقم الجوال', validators=[validate_phone])
    code = forms.CharField(label='رمز التحقق', validators=[validate_code],
                           widget=forms.TextInput(attrs={'autofocus': True}))

    class Meta:
        fields = ('phone', 'code')


class NewPasswordForm(forms.Form):
    password1 = forms.CharField(label='كلمة المرور الجديدة', widget=forms.PasswordInput(attrs={'autofocus': True}))
    password2 = forms.CharField(label='تأكيد كلمة المرور', widget=forms.PasswordInput())

    class Meta:
        fields = ('password1', 'password2')
        help_texts = {'password1': 'أدخل كلمة المرور الجديدة'}

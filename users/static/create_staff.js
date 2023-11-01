$(function (){

    // translate the labels and hints of the form

    const password1_label = $('#div_id_password1 label');
    password1_label.text('كلمة المرور');

    const password2_label = $('#div_id_password2 label');
    password2_label.text('تأكيد كلمة المرور');

    const hintsList = $('#hint_id_password1 ul');

    const hint = hintsList.children().first();
    hint.text('يجب ألا تكون كلمة المرور متشابهة مع معلوماتك الشخصية ');
    const hint2 = hint.next();
    hint2.text('يجب أن تحتوي كلمة المرور على 8 أحرف على الأقل');
    const hint3 = hint2.next();
    hint3.text('يجب ألا تكون كلمة المرور شائعة الاستخدام');
    const hint4 = hint3.next();
    hint4.text('يجب ألا تتكون كلمة المرور مكونة من أرقام فقط');

    const password2_hint =$('#hint_id_password2');
    password2_hint.text('أدخل نفس كلمة المرور كما في الأعلى، للتأكيد');


})
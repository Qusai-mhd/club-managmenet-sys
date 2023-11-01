window.onload = function() {

    // Translate and Shorten the labels
    var labels = document.getElementsByTagName("label");
    for (var i = 0; i < labels.length; i++) {
        var currentLabel = labels[i];

        for (var j = 0; j < currentLabel.childNodes.length; j++) {
            // loop through all the child nodes of the current label
            var childNode = currentLabel.childNodes[j];
            // if the child node is a text node and contains a text replace it with a shorter one.
            if (childNode.nodeType === Node.TEXT_NODE) {
                if (childNode.nodeValue.indexOf("add reservation") !== -1){
                    childNode.nodeValue = "بإمكانه إنشاء وتعديل الحجوزات";
                }
                else if (childNode.nodeValue.indexOf("add facility") !== -1){
                    childNode.nodeValue = "بإمكانه تسجيل وتعديل الملاعب";
                }
                else if (childNode.nodeValue.indexOf("add time slot") !== -1){
                    childNode.nodeValue = "بإمكانه إنشاء وتعديل الفترات";
                }
                else if (childNode.nodeValue.indexOf("تقرير") !== -1){
                    childNode.nodeValue = "بإمكاته إنشاء وعرض التقارير";
                }
                else if (childNode.nodeValue.indexOf("reservation | بإمكانه تغيير السعر") !== -1){
                    childNode.nodeValue = "بإمكاته تغيير السعر عند إنشاء الحجز";
                }

                else if (childNode.nodeValue.indexOf("session record") !== -1){
                    childNode.nodeValue = "بإمكانه إنشاء وتعديل سجل الحضور";
                }
                else if (childNode.nodeValue.indexOf("add division") !== -1){
                    childNode.nodeValue = "بإمكانه إنشاء وتعديل الفئات";
                }
                else if (childNode.nodeValue.indexOf("Can add subscription") !== -1){
                    childNode.nodeValue = "بإمكانه إنشاء وتعديل الإشتراكات";
                }
                else if (childNode.nodeValue.indexOf("Can view subscription") !== -1){
                    childNode.nodeValue = "بإمكانه عرض الإشتراكات";
                }
                else if (childNode.nodeValue.indexOf("بإمكانه تغيير السعر") !== -1){
                    childNode.nodeValue = 'بإمكانه تغير سعر الاشتراك';
                }
                else if (childNode.nodeValue.indexOf("week day") !== -1){
                    childNode.nodeValue = 'بإمكانه إنشاء وتعديل أيام التدريب';
                }

            }

        }
    }


    // place a break tag before the help text element
    const helptext = $(".helptext");
    helptext.before("<br>");

    // if the is_superuser checkbox is checked then hide the reset of the permissions
    const isSuperuser = $("#id_is_superuser");
    if (isSuperuser.is(':checked')) {
        const form = $('#permissions_form');
        form.children().not(":first").not(":first").not(":last").hide();
    }

    // listen to the change event of the is_superuser checkbox
    isSuperuser.change(function() {
        const form = $('#permissions_form');
        if (isSuperuser.is(':checked')) {
            form.children().not(":first").not(":first").not(":last").hide();
        }
        else {
            form.children().show();
        }
    });
}

$( function (){
    // Translate the delete labels
    const delete_labels = $("label:contains('Delete:')")
    delete_labels.each(function(){
        $(this).html('حذف')
    });


    // get all the checkboxes with the name that contains '-DELETE'
    const delete_checkboxes = $("input[name*='-DELETE']");

    const delete_all = $('#deleteAll');
    delete_all.change(function() {
        const checked = $(this).prop('checked');

        if (checked){
            // set all the checkboxes to checked
            delete_checkboxes.prop('checked', true);
        } else {
            delete_checkboxes.prop('checked',false);
        }
    });

    // if any of the checkboxes is unchecked, uncheck the delete_all checkbox
    delete_checkboxes.change(function(){
        const checked = $(this).prop('checked');
        if (!checked){
            // set the delete_all checkbox to unchecked
            delete_all.prop('checked', false);
        }
        else {
            // check if all the checkboxes are checked, if so, check the delete_all checkbox
            let all_checked = true;
            delete_checkboxes.each(function(){
                const isChecked = $(this).prop('checked');
                if (!isChecked){
                    all_checked = false;
                }
            });
            if (all_checked){
                delete_all.prop('checked', true);
            }
        }
    });
})
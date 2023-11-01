document.addEventListener('DOMContentLoaded', function() {


    // get the parent element of the elements with id id_month and id_year and id_dayFrom and id_dayTo
    const monthSelection = $('#div_id_month');
    const yearSelection = $('#div_id_year');
    const dayFromSelection = $('#div_id_dayFrom');
    const dayToSelection = $('#div_id_dayTo');

    // get the radio button named reportPeriod
    const reportPeriod = $('input[type=radio][name="reportPeriod"]');

    monthSelection.show();
    yearSelection.show();
    dayFromSelection.hide();
    dayToSelection.hide();

    // listen for change event on the radio button
    reportPeriod.change(function() {
        // get the value of the selected radio button
        const selectedValue = this.value;

        // monthly, yearly, custom

        if (selectedValue === 'monthly') {
            monthSelection.show();
            yearSelection.show();
            dayFromSelection.hide();
            dayToSelection.hide();
        }
        else if (selectedValue === 'yearly') {
            monthSelection.hide();
            yearSelection.show();
            dayFromSelection.hide();
            dayToSelection.hide();
        }
        else if (selectedValue === 'custom') {
            monthSelection.hide();
            yearSelection.hide();
            dayFromSelection.show();
            dayToSelection.show();
        }
    })

    const radioDivs = $('.form-check');
    radioDivs.addClass('form-check-inline');

    const radios = $('input[type=radio]');
    radios.addClass('mx-2');

})

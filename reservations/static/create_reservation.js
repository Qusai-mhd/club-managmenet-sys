$(function () {
    console.log("create_reservation.js loaded")
    const form = $('#reservation_form');
    const facility_input = $('input[type=radio][name="0-facility"]');
    const day_input = $('#id_0-day');

    if (isSingleCreateView){
        // auto submit the first form:
        if (facility_input.length && day_input.length){
            facility_input.change(checkFields);
            day_input.change(checkFields);

            const dateRegex =  /^202[0-9]-[01]?[0-9]-[0-3]?[0-9]$/;

            function checkFields() {
                // Check if both fields have values
                if (facility_input.is(':checked') && dateRegex.test(day_input.val())) {
                    form.submit();
                }
            }
        }
    }
});

document.addEventListener('DOMContentLoaded', function() {

    //  grap all the date input fields
    const dateInputs = $('input[type=date]');
    // grap the dateInputs parents
    const dateInputsParents = dateInputs.parent();

    const facilityInputParent = $('#id_facility').parent();
    const categoryInputParent = $('#id_category').parent();
    categoryInputParent.hide();


    // get the URL parameter named searchByDay
    const urlParams = new URLSearchParams(window.location.search);
    const searchByDayParam = urlParams.get('searchByDay');
    const searchByPriceParam = urlParams.get('searchByPrice');
    const searchByFacilityParam = urlParams.get('searchByFacility');


    // if searchByDay is value 'range' show the second and third dateInputParent and hide the rest
    if (searchByDayParam === 'range') {
        dateInputsParents.eq(0).hide();
        dateInputsParents.eq(1).show();
        dateInputsParents.eq(2).show();
    }
    else {
        dateInputsParents.first().show();
        dateInputsParents.not(':eq(0)').hide();
    }

    if (searchByFacilityParam === 'facility') {
        facilityInputParent.show();
        categoryInputParent.hide();
    }
    else if (searchByFacilityParam === 'category') {
        facilityInputParent.hide();
        categoryInputParent.show();
    }

    // if searchByFacility is value 'facility' show the second and third dateInputParent and hide the rest


    // get the radio button named searchByDay
    const searchByDay = $('input[type=radio][name="searchByDay"]');

    // listen for change event on the radio button
    searchByDay.change(function() {
        // get the value of the selected radio button
        const selectedValue = this.value;

        // if the value is 'exact' or 'before' or 'after', show the first date input parent and hide the rest
        if (selectedValue === 'exact' || selectedValue === 'before' || selectedValue === 'after') {
            dateInputsParents.first().show();
            dateInputsParents.not(':eq(0)').hide();
        }
        // if the value is 'range' show the second and third dateInputParent and hide the rest
        else if (selectedValue === 'range') {
            dateInputsParents.eq(0).hide();
            dateInputsParents.eq(1).show();
            dateInputsParents.eq(2).show();
        }

    })

    const searchByFacility = $('input[type=radio][name="searchByFacility"]');
    searchByFacility.change(function() {

        const selectedValue = this.value;

        if (selectedValue === 'facility') {
            facilityInputParent.show();
            categoryInputParent.hide();
        }
        else if (selectedValue === 'category') {
            facilityInputParent.hide();
            categoryInputParent.show();
        }
    });


    // grap all the number input fields
    const numberInputs = $('input[type=number]');

    // grap the numberInputs parents
    const numberInputsParents = numberInputs.parent();


    // if searchByPrice is value 'range' show the second and third numberInputParent and hide the rest
    if (searchByPriceParam === 'range') {
        numberInputsParents.eq(0).hide();
        numberInputsParents.eq(1).show();
        numberInputsParents.eq(2).show();
    }
    else {
        numberInputsParents.first().show();
        numberInputsParents.not(':eq(0)').hide();
    }


    // get the radio button named searchByPrice
    const searchByPrice = $('input[type=radio][name="searchByPrice"]');

    // listen for change event on the radio button
    searchByPrice.change(function() {
        // if the value is 'exact' or 'less' or 'greater', show the first number input parent and hide the rest
        if (this.value === 'exact' || this.value === 'less' || this.value === 'greater') {
            numberInputsParents.first().show();
            numberInputsParents.not(':eq(0)').hide();
        }
        // if the value is 'range' show the second and third numberInputParent and hide the rest
        else if (this.value === 'range') {
            numberInputsParents.eq(0).hide();
            numberInputsParents.eq(1).show();
            numberInputsParents.eq(2).show();
        }
    })
})

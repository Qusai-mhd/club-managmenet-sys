$(function (){

    const division = $('select[name="division"]');
    const price_input = $('#id_price');

    // when a new division is selected
    if (division.length) {
        division.change(function () {
            const division_id = $(this).val();
            // send an ajax request to get the price of the selected division
            $.ajax({
                url: 'get-division-price?division_id=' + division_id,
                success: function (data) {
                    price_input.val(data.price);
                    calculateTotalPrice();
                },
                error: function (xhr, textStatus, errorThrown) {
                    price_input.val('0.00');
                    calculateTotalPrice()
                }
            })
        });
    }

    const months_number = $('#id_months_num')
    const total_price = $('#id_total_price');

    const calculateTotalPrice = function (){
        const price = parseFloat(price_input.val());
        const months = parseInt(months_number.val());
        total_price.val(price * months);
    };

    months_number.keyup(calculateTotalPrice);
    price_input.keyup(calculateTotalPrice);
});

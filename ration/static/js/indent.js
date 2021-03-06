$(document).ready(function(){

    // 1. Visualizing things on Hover
    $("#flames li").on('mouseover', function(){
        var onFlame = parseInt($(this).data('value'),10);

            // Now highlight all that's not after the current hovered flame
        $(this).parent().children('li.flame').each(function(e){
            if (e < onFlame) {

            $(this).addClass('hover');
            } else {
                $(this).removeClass('hover');
            }
        });

    }).on('mouseout', function(){
        $(this).parent().children('li.flame').each(function(e){
            $(this).removeClass('hover');
        });
    });

    // 2. Action to perform on click
    $('#flames li').on('click', function(){
        var onFlame = parseInt($(this).data('value'), 10);
        var flames = $(this).parent().children('li.flame');

        for (i = 0; i < flames.length; i++){
            $(flames[i]).removeClass('selected');
        }

        for (i = 0; i < onFlame; i++){
            $(flames[i]).addClass('selected');
        }

        // AJAX
        var interestValue = parseInt($('#flames li.selected').last().data('value'), 10);
        var form_data = {
            csrfmiddlewaretoken: '{{ csrf_token }}',
            interest: interestValue,
            user_id: "{{ request.user.id }}",
            item_id: "{{ item.id }}"
        }

        update_interest(form_data);

    });

});

function update_interest(form_data){
    $.ajax({
        url: "/ajax/update_rating",
        type: "POST",
        data: form_data,
        dataType: 'json',

        success : function(data){
            console.log(data.message)
        }
    });
};
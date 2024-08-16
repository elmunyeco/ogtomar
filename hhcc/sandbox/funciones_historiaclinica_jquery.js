$(document).ready(function(){

    // Copiar Indicaciones de un Paciente
    $('.copiarIndicacion').click(function(){
        $('.copiarIndicacion').hide();
        $('#panelLoading').show().css('display', 'block');

        $.ajax({
            type: "POST",
            url: $(this).attr('href'),
            success: function(data) {
                $("[name='tipoComentario']").each( function() { 
                    if ( $(this).val() == 2 )
                        $(this).attr('checked', true);
                });

                $('#comentarioIndicacion').html(data);
                $('#panelLoading').hide();
            }
        });

        return false;
    });

    // Manejo del Formulario de Diagnóstico
    $('#formDiagnostico').submit(function(){
        $('.guardarComentario').hide();
        $('#enfLoading').addClass('glyphicon-refresh-animate');

        $.ajax({
            type: "POST",
            url: $(this).attr('action'),
            data: $(this).serialize(),
            success: function(data) {
                $('.guardarComentario').show();
                $('#enfLoading').removeClass('glyphicon-refresh-animate');
            }
        });

        return false;
    });

    $('.chEnfermedades').change(function(){
        $('#formDiagnostico').submit();
    });

    // Gestión de Comentarios
    $('.guardarComentarioIndicacion').click(function(){		
        var comentario = $('#comentario').val();
        if(comentario.trim() == "") {
            $('.msjError').html("Debe completar el comentario").show();
            return false;
        }
        
        var idHC = $('#idHC').val();
        var proteger = $('.comentarioCheckbox:checked').val();
        if (proteger == undefined) {
            proteger = 0;
        }
        
        $('.msjError, .msjIndicacion').hide();
        
        $.ajax({
            type: "POST",
            url: $(this).attr('href'),
            data: {idHC: idHC, comentario: comentario, proteger: proteger, eliminado : 0},
            dataType: "json",
            success: function(data) {
                if(data.exito) {
                    $('.msjIndicacion').html(data.msj).show();
                } else {
                    $('.msjError').html(data.msj).show();
                }
            },
            error: function(){
                $('.msjError').html("Se produjo un error al realizar el proceso. Inténtelo nuevamente más tarde.").show();
            }
        });

        return false;
    });

    // Eliminar Comentarios
    $('.eliminarComentario').click(function(){
        $(this).hide();
        $(this).parent().find('span').css('display', 'inline');

        var id = $(this).attr('id');
        
        $.ajax({
            type: "POST",
            url: $(this).attr('href'),
            success: function(data) {
                $('#comentario_' + id ).remove();
            }
        });

        return false;
    });

    // Acordeón para Detalles de la Historia Clínica
    $('.collapsed').click(function(){
        if($(this).prev().hasClass('glyphicon-chevron-down'))
            $(this).prev().removeClass('glyphicon-chevron-down').addClass('glyphicon-chevron-right');
        else {
            $('[data-toggle="collapse"]').each(function(index, item){
                $(this).prev().removeClass('glyphicon-chevron-down').addClass('glyphicon-chevron-right');
            });

            $(this).prev().removeClass('glyphicon-chevron-right').addClass('glyphicon-chevron-down');
        }

        var top = $(this).offset().top;
        $('html, body').animate({scrollTop: top},1000);
        var nodo = $(this).attr('href');
    });

});

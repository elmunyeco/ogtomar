$(document).ready(function() {

	/* INICIALIZO LIBRERIAS JAVACRIPT */
	$('.map').maphilight({
		fillColor: '999999',
		fillOpacity: 0.6,
		strokeColor: '000000'
	});

	/*******************************************************************************************/
	/* PACIENTE */
	/*******************************************************************************************/
	/*$('#formPaciente').submit(function(){

		//if(validarPaciente()){

			var action   = $(this).attr('action');
			var idHC	 = $('#idHC').val();
			$('.divBtnsPaciente .btn').attr('disabled', 'disabeld');
			$('#spnGuardar').html('Guardando...');
			$('#ldgGuardar').css('display', 'inline-block');

			$.ajax({
				   
			    type: "POST",
			    url: action,
			    data: $(this).serialize(),
			    dataType: "json",
			    async: false, 
			    success: function(data) {
				   	
					if(data) {
						$('.idEco').val(data);
						$('#msjPaciente').removeClass('bg-danger').addClass('bg-success').html('Los datos del paciente se han guardado correctamente.').show();
					} else {
						$('#msjPaciente').removeClass('bg-success').addClass('bg-danger').html('Error al guardar los datos del paciente.').show();
					}

					$('#ldgGuardar').hide();
					$('#spnGuardar').html('Guardar').show();
					$('.divBtnsPaciente .btn').removeAttr('disabled');
			    },
			    error: function(){
			    	$('#msjPaciente').show();
					$('#ldgGuardar').hide();
					$('#spnGuardar').html('Guardar').show();
					$('.divBtnsPaciente .btn').removeAttr('disabled');
			    }
			});

		//}

		return false;
	});
	*/

	/*******************************************************************************************/
	/* Informe ECO */
	/*******************************************************************************************/
	$('.btnSbtEco').click(function(){

		$('.divBtns .btn').attr('disabled', 'disabeld');
		$('#spnGuardarEco').html('Guardando...');
		$('#ldgGuardarEco').css('display', 'inline-block');

		/* Cargo los datos del paciente para obtener el ID del estudio de ECO */
		//$('#formPaciente').trigger('submit');
		var action   = $('#formPaciente').attr('action');
		var idHC	 = $('#idHC').val();
		$('.divBtnsPaciente .btn').attr('disabled', 'disabeld');
		$('#spnGuardar').html('Guardando...');
		$('#ldgGuardar').css('display', 'inline-block');

		$.ajax({
			   
		    type: "POST",
		    url: action,
		    data: $('#formPaciente').serialize(),
		    dataType: "json",
		    async: false, 
		    success: function(data) {
			   	
				if(data) {
					$('.idEco').val(data);
					$('#msjPaciente').removeClass('bg-danger').addClass('bg-success').html('Los datos del paciente se han guardado correctamente.').show();
				} else {
					$('#msjPaciente').removeClass('bg-success').addClass('bg-danger').html('Error al guardar los datos del paciente.').show();
				}

				$('#ldgGuardar').hide();
				$('#spnGuardar').html('Guardar').show();
				$('.divBtnsPaciente .btn').removeAttr('disabled');
		    },
		    error: function(){
		    	$('#msjPaciente').show();
				$('#ldgGuardar').hide();
				$('#spnGuardar').html('Guardar').show();
				$('.divBtnsPaciente .btn').removeAttr('disabled');
		    }
		});

		/* Cargo los datos en la tabla bidimensional */
		var action   = $('#formBidimensional').attr('action');
		var idHC	 = $('#idHC').val();

		$.ajax({
			   
		    type: "POST",
		    url: action,
		    data: $('#formBidimensional').serialize(),
		    dataType: "json",
		    success: function(data) {
			   	
				if(data) {
					$('#msjBidimensional').removeClass('bg-danger').addClass('bg-success').html('Los datos se han guardado correctamente.').show();
				} else {
					$('#msjBidimensional').removeClass('bg-success').addClass('bg-danger').html('Error al guardar los datos del informe.').show();
				}

				$('#ldgGuardarEco').hide();
				$('#spnGuardarEco').html('Guardar').show();
				$('.divBtns .btn').removeAttr('disabled');
		    },
		    error: function(){
		    	$('#msjBidimensional').removeClass('bg-success').addClass('bg-danger').html('Error al guardar los datos del informe.').show();
				$('#ldgGuardarEco').hide();
				$('#spnGuardarEco').html('Guardar').show();
				$('.divBtns .btn').removeAttr('disabled');
		    }
		});

		/* Cargo los datos en la tabla de Coppler */
		action   = $('#formCoppler').attr('action');

		$.ajax({
			   
		    type: "POST",
		    url: action,
		    data: $('#formCoppler').serialize(),
		    dataType: "json",
		    success: function(data) {
			   	
				if(data) {
					$('#msjCoppler').removeClass('bg-danger').addClass('bg-success').html('Los datos se han guardado correctamente.').show();
				} else {
					$('#msjCoppler').removeClass('bg-success').addClass('bg-danger').html('Error al guardar los datos del informe.').show();
				}

				$('#ldgGuardarEco').hide();
				$('#spnGuardarEco').html('Guardar').show();
				$('.divBtns .btn').removeAttr('disabled');
		    },
		    error: function(){
		    	$('#msjCoppler').removeClass('bg-success').addClass('bg-danger').html('Error al guardar los datos del informe.').show();
				$('#ldgGuardarEco').hide();
				$('#spnGuardarEco').html('Guardar').show();
				$('.divBtns .btn').removeAttr('disabled');
		    }
		});

		/* Cargo los datos en la tabla de Segmentos */
		action   = $('#formSegmentos').attr('action');
		
		$.ajax({
			   
		    type: "POST",
		    url: action,
		    data: $('#formSegmentos').serialize(),
		    dataType: "json",
		    success: function(data) {
			   	
				if(data) {
					$('#msjSegmentos').removeClass('bg-danger').addClass('bg-success').html('Los datos se han guardado correctamente.').show();
				} else {
					$('#msjSegmentos').removeClass('bg-success').addClass('bg-danger').html('Error al guardar los datos del informe.').show();
				}

				$('#ldgGuardarEco').hide();
				$('#spnGuardarEco').html('Guardar').show();
				$('.divBtns .btn').removeAttr('disabled');
		    },
		    error: function(){
		    	$('#msjSegmentos').removeClass('bg-success').addClass('bg-danger').html('Error al guardar los datos del informe.').show();
				$('#ldgGuardarEco').hide();
				$('#spnGuardarEco').html('Guardar').show();
				$('.divBtns .btn').removeAttr('disabled');
		    }
		});

		/* Cargo los datos en la tabla de conclusiones */
		action   = $('#formConclusiones').attr('action');
		
		$.ajax({
			   
		    type: "POST",
		    url: action,
		    data: $('#formConclusiones').serialize(),
		    dataType: "json",
		    success: function(data) {
			   	
				if(data) {
					$('#msjConclusiones').removeClass('bg-danger').addClass('bg-success').html('Los datos se han guardado correctamente.').show();
				} else {
					$('#msjConclusiones').removeClass('bg-success').addClass('bg-danger').html('Error al guardar los datos del informe.').show();
				}

				$('#ldgGuardarEco').hide();
				$('#spnGuardarEco').html('Guardar').show();
				$('.divBtns .btn').removeAttr('disabled');
		    },
		    error: function(){
		    	$('#msjConclusiones').removeClass('bg-success').addClass('bg-danger').html('Error al guardar los datos del informe.').show();
				$('#ldgGuardarEco').hide();
				$('#spnGuardarEco').html('Guardar').show();
				$('.divBtns .btn').removeAttr('disabled');
		    }
		});

		/* Cargo el comentario final */
		action   = $('#formFinal').attr('action');

		$.ajax({
			   
		    type: "POST",
		    url: action,
		    data: $('#formFinal').serialize(),
		    dataType: "json",
		    async: false, 
		    
		    success: function(data) {
			   	
				if(data) {
					$('#msjComFinal').removeClass('bg-danger').addClass('bg-success').html('Los datos se han guardado correctamente.').show();
				} else {
					$('#msjComFinal').removeClass('bg-success').addClass('bg-danger').html('Error al guardar los datos del informe.').show();
				}

				$('#ldgGuardarEco').hide();
				$('#spnGuardarEco').html('Guardar').show();
				$('.divBtns .btn').removeAttr('disabled');
		    },
		    error: function(){
		    	$('#msjComFinal').removeClass('bg-success').addClass('bg-danger').html('Error al guardar los datos del informe.').show();
				$('#ldgGuardarEco').hide();
				$('#spnGuardarEco').html('Guardar').show();
				$('.divBtns .btn').removeAttr('disabled');
		    }
		});
		
		/* Cargo la conclusionB */
		action   = $('#formConclB').attr('action');

		$.ajax({
			   
		    type: "POST",
		    url: action,
		    data: $('#formConclB').serialize(),
		    dataType: "json",
		    async: false, 
		    
		    success: function(data) {
			   	
				if(data) {
					$('#msjConclusionesB').removeClass('bg-danger').addClass('bg-success').html('Los datos se han guardado correctamente.').show();
				} else {
					$('#msjConclusionesB').removeClass('bg-success').addClass('bg-danger').html('Error al guardar los datos del informe.').show();
				}

				$('#ldgGuardarEco').hide();
				$('#spnGuardarEco').html('Guardar').show();
				$('.divBtns .btn').removeAttr('disabled');
		    },
		    error: function() { 
		    	$('#msjConclusionesB').removeClass('bg-success').addClass('bg-danger').html('Error al guardar los datos del informe.').show();
				$('#ldgGuardarEco').hide();
				$('#spnGuardarEco').html('Guardar').show();
				$('.divBtns .btn').removeAttr('disabled');
		    }
		});
    
		var url = action.substr(0, action.lastIndexOf('/')) + '/imprimirEstudio/' + $('.idEco').val() + "/" + idHC;
		
		window.open(url);
		return false;
	});
	
	/*******************************************************************************************/
	/* TAB */
	/*******************************************************************************************/
	$('ul.nav-tabs li a').click(function(){

		$('ul.nav-tabs li').removeClass('active');
		$( this ).parent().addClass('active');
		var ref = $( this ).attr('href');
		$('.tabs').hide();
		$('.'+ ref).show();
		return false;
	});

	/*******************************************************************************************/
	/* SEGMENTOS */
	/*******************************************************************************************/
	// Cuando hago click en el area muestro la lista de valores que puedo elegir para el segmento 
	$('area').click(function(){

		$('.valorSegmento').attr('checked', false);	
		$('#modal').modal('show');
		var valor = $(this).attr('id').substr(8);

		// Para los casos en los que encuentro un "_bis", me quedo solo con el numero
		if(valor.length > 2)
			valor = valor.substr(0, (valor.length - 4));

		$('#idSegmento').val(valor);
		return false;
	});

	$('#modal').on('hide.bs.modal', function (e) {

		var valor = $(".valorSegmento:checked").val();

		if(valor)
		{
			var nodo  = $('#segmento' + $('#idSegmento').val());
			var data  = $(nodo).mouseout().data('maphilight') || {};
			var color = getColorSegmento(valor);
			$( '#sOculto' + $('#idSegmento').val() ).val(valor);
			
			data.fillColor 		= color
			data.alwaysOn 		= true;
			data.fillOpacity	= 0.6;
			$(nodo).data('maphilight', data).trigger('alwaysOn.maphilight');
			
			// Coloreo los segmentos que se repiten en varias imagenes
			var num =  $('#idSegmento').val();
			
			if($('#segmento' + num + '_bis').length > 0){
				nodo  = $('#segmento' + num + '_bis');
				var data  = $(nodo).mouseout().data('maphilight') || {};
				
				data.fillColor 		= color;
				data.alwaysOn 		= true;
				data.fillOpacity	= 0.6;
				$(nodo).data('maphilight', data).trigger('alwaysOn.maphilight');
			}
		}
	})

	$('#allNormal').change(function(){
		var color;
		var alwaysOn;
		var valor;
		var cantSegmentos = 16;
		var arrayRepetidos = [2,4,7,10,12,15]; // Array con los segmentos que se repiten en varias imágenes

		if($(this).prop('checked')){
			color = 'FFFF00';
			valor = 1;
			alwaysOn = true;
		} else {
			color = '999999';
			valor = 0;
			alwaysOn = false;
		}

		// Modifico el color y valor de la lista de todos los segmentos
		for (var i = 1; i <= cantSegmentos; i++) {

			var data  		= $('#segmento' + i).mouseout().data('maphilight') || {};
			var nodoLista	= $('#segmento' + i).next();
			nodoLista.val(valor);
			data.fillColor 	= color;
			data.alwaysOn 	= alwaysOn;
			$( '#sOculto' + i ).val(valor);
	        $('#segmento' + i).data('maphilight', data).trigger('alwaysOn.maphilight');
		};

		// Coloreo los segmentos que se repiten en varias imagenes
		for (var i = 0; i < arrayRepetidos.length; i++) {
			var ind = arrayRepetidos[i];
			var data  		= $('#segmento' + ind + "_bis").mouseout().data('maphilight') || {};
			var nodoLista	= $('#segmento' + ind + "_bis").next();
			nodoLista.val(valor);
			data.fillColor 	= color;
			data.alwaysOn 	= alwaysOn;
	        $('#segmento' + ind + "_bis").data('maphilight', data).trigger('alwaysOn.maphilight');
		};

	});

	$('#modal input').change(function(){
		$('#modal').modal('hide');
	});


	/*******************************************************************************************/
	/* CONCLUSIONES */
	/*******************************************************************************************/
	// Para cuando elijo algo de las listas
	$('.divConclusiones select.form-control').change(function(){

		var orden = $(this).attr('data-orden');

		if($(this).val())
		{
			var contenido 	= "";
			var indice 		= "";

			indice 	  = $( this ).val();

			if( indice )
				contenido = $( 'select[data-orden="' + orden + '"] option:selected' ).text();
			
			$('.itemO_' + orden).val(indice);			

			// Verifico si estoy actualizando el valor para esta conclusion, si es así solo cambio el valor que tengo
			// en la clase item_[orden], de lo contrario lo cargo.
			if($('.item_' + orden).length > 0) {
				
				$('.item_' + orden).html(contenido);

			} else {

				var padre = $(this).parent().prev().html();
				var valor = "<b>" + padre + "</b> <span class='item_"+ orden + "'>" + contenido + "</span>";

				$('.boxConclusiones .orden_' + orden).html(valor);

				// Habilito el comentario, si es que tiene
				if($('textarea[data-orden="' + orden + '"]').length > 0)
					$('textarea[data-orden="' + orden + '"]').parent().show();
			}
		} else {

			// Si no elijo nada de la lista debo ocultar el comentario, si es que tiene y quitar el contenido que hay
			if($('textarea[data-orden="' + orden + '"]').length > 0){

				$('textarea[data-orden="' + orden + '"]').parent().hide();
			}

			$('.orden_' + orden).html('');
			$('.itemO_' + orden).val('');
		}

	});

	$('.auriculaIzq, .ventriculoIzq').change(function(){

		var orden = $(this).parent().parent().attr('data-orden');
		var contenido 	= "";
		var indice 		= "";
		var clase 		= $(this).attr('class');
		var indices 	= "";

		$('.' + clase +':checked').each(function(index, item) {
			
			if($(this).val())
			{
				indice 	  = $( this ).val();

				if ( index){

					contenido += ", ";
					indices += ", ";
				}

				indices	  += indice;
				contenido += $( '.' + clase +'[value="' + indice + '"]' ).next('label').text();
			}
		});

		$('.itemO_' + orden).val(indices);

		if(contenido) {

			// Verifico si estoy actualizando el valor para esta conclusion, si es así solo cambio el valor que tengo
			// en la clase item_[orden], de lo contrario lo cargo.
			if($('.item_' + orden).length > 0) {
				
				$('.item_' + orden).html(contenido);

			} else {

				var padre = $(this).parent().parent().prev().html();
				var valor = "<b>" + padre + "</b> <span class='item_"+ orden + "'>" + contenido + "</span>";

				$('.boxConclusiones .orden_' + orden).html(valor);
			}
		}
	});

	$('#conclusionesB').on( "keyup", function(e){
		
		var restante = 1500 - $(this).val().length;
		
		if(restante < 1)
			$('#faltantesB').html(0);
		else
			$('#faltantesB').html(restante);
			
	});
  
  $('#comentarioFinal').on( "keyup", function(e){
		
		var restante = 700 - $(this).val().length;
		
		if(restante < 1)
			$('#faltantes').html(0);
		else
			$('#faltantes').html(restante);
			
	});

	// Para cuando agrego algún comentario
	$('.divConclusiones textarea').change(function(){

		var orden = $(this).attr('data-orden');

		if($('.boxConclusiones .orden_' + orden).html() != '')
		{
			if($('.comentario_' + orden).length > 0) {
				
				$('.comentario_' + orden).html($(this).val());

			} else {

				var orden = $(this).attr('data-orden');
				var padre = $(this).parent().prev().prev().html();
				var valor = $('.boxConclusiones .orden_' + orden).html() + ". <span class='comentario_" + orden + "'>" + $(this).val() + "</span><br>";

				$('.boxConclusiones .orden_' + orden).html(valor);
				
			}
		}

		$('.hideCom_' + orden).val($(this).val());
	});

	$('input').change(function(){
		$(this).val($(this).val().replace(',', '.'));
	});

	/* VALORES CALCULABLES */
	//Superficie Corporal
	$('#inputPeso, #inputTalla').change(function(){
		getSupCorporal();
	});	

	//Fraccion de acortamiento
	$('#ventIzqDiastolico, #ventIzqSistolico').change(function(){
		getFraccionAcortamiento();
	});
	
	// Para obtener el gradiente 
	$('#valvulaPulmonar, #valvulaAortica, #tractoVentIzq').change(function(){
		getGradiente( $(this).val(), $('#' + $(this).attr('class')) );
	});

	// Para obtener el gradiente de las ondas
	$('#ondaEMitral, #ondaETricuspidea').change(function(){
		getGradiente( $(this).val(), $('#' + $(this).attr('class')) );
	});


	/*****************************************************************/
	/* FUNCIONES QUE SE EJECUTAN CADA VEZ QUE SE CARGA LA PÁGINA*/
	/*****************************************************************/
	getSupCorporal();
	getFraccionAcortamiento();
	$('#valvulaPulmonar, #valvulaAortica, #tractoVentIzq').trigger('change');
	$('#ondaEMitral, #ondaETricuspidea').trigger('change');
	$('.divConclusiones select.form-control').trigger('change');
	$('.divConclusiones textarea').trigger('change');
	$('.auriculaIzq, .ventriculoIzq').trigger('change');
	$('ul.nav-tabs li.active a').trigger('click');
	$('#comentarioFinal').trigger('keyup');
  $('#conclusionesB').trigger('keyup');
	colorearSegmentos();


	// Footer
	var height = $('body').height();
	var hWindow = $(window).height();

	if( height < hWindow)
		$('.footer').addClass('bottom');
	
});


/*****************************************************************/
/* FUNCIONES */
/*****************************************************************/
function getSupCorporal()
{
	var peso  		= $('#inputPeso').val();
	var talla 		= $('#inputTalla').val();
	var superficie	= '';

	if( peso != '' && talla != '' )
	{
		superficie = parseFloat(peso / (talla * talla));
        //superficie =  superficie.toFixed(2);
        superficie = Math.ceil(superficie);
	}

	$('#supCorporal').html(superficie);	
}

function getFraccionAcortamiento()
{
	var diastolico  = $('#ventIzqDiastolico').val();
	var sistolico 	= $('#ventIzqSistolico').val();
	var fracion		= '';

	if( diastolico != '' && sistolico != '' )
	{
		fracion = (( diastolico - sistolico ) / diastolico ) * 100;
        fracion = Math.ceil(fracion);
	}

	$('#fraccionAcortamiento').html(fracion);
	$('#fraccionAcorHidden').val(fracion);
}


function getGradiente( valor, nodo )
{
	var gradiente	= '';
	var unidad		= '';

	if( valor != '')
	{
		gradiente = ( valor * valor )  * 4;
        //gradiente =  gradiente.toFixed(2);
        gradiente = Math.ceil(gradiente);
        unidad	  = " mmHg";
	}

	$(nodo).html(gradiente + unidad);
}

function getColorSegmento( valor )
{
	switch(valor){
		case '0':
			return 'FFFFFF';
		case '1':
			return 'FFFF00';
		case '2':
			return 'FF7700';
		case '3':
			return 'FF0000';
		case '4':
			return '0000FF';
	}
}

function validarPaciente()
{
	var peso 	= $('#inputPeso');
	var talla 	= $('#inputTalla');
	var pad 	= $('#inputPad');
	var pas 	= $('#inputPas');
	var res 	= true;

	if($.trim(peso.val()) == '' || peso.val() == null){
		peso.parent().parent().addClass('has-error has-feedback');
		peso.focus();
		res 	= false;
	} else {
		peso.parent().parent().removeClass('has-error has-feedback');
	}

	if($.trim(talla.val()) == '' || talla.val() == null){
		talla.parent().parent().addClass('has-error has-feedback');
		
		if(res)
			talla.focus();

		res 	= false;
	} else {
		talla.parent().parent().removeClass('has-error has-feedback');
	}

	if($.trim(pas.val()) == '' || pas.val() == null){
		pas.parent().parent().addClass('has-error has-feedback');

		if(res)
			pas.focus();

		res 	= false;
	} else {
		pas.parent().parent().removeClass('has-error has-feedback');
	}

	if($.trim(pad.val()) == '' || pad.val() == null){
		pad.parent().parent().addClass('has-error has-feedback');
		
		if(res)
			pad.focus();

		res 	= false;
	} else {
		pad.parent().parent().removeClass('has-error has-feedback');
	}

	return res;
}

// Función encargada de colorear los segmentos cuando se está editando un estudio
function colorearSegmentos()
{
	var cant = 16;

	for (var i = 1; i <= cant; i++) {
		
		if($( '#sOculto' + i ).val()){


			var nodo  = $('#segmento' + i);
			var data  = $(nodo).mouseout().data('maphilight') || {};
			var color = getColorSegmento($( '#sOculto' + i ).val());
						
			data.fillColor 		= color
			data.alwaysOn 		= true;
			data.fillOpacity	= 0.6;
			$(nodo).data('maphilight', data).trigger('alwaysOn.maphilight');
			
			// Coloreo los segmentos que se repiten en varias imagenes
			var num =  i;
			
			if($('#segmento' + num + '_bis').length > 0){
				nodo  = $('#segmento' + num + '_bis');
				var data  = $(nodo).mouseout().data('maphilight') || {};
				
				data.fillColor 		= color;
				data.alwaysOn 		= true;
				data.fillOpacity	= 0.6;
				$(nodo).data('maphilight', data).trigger('alwaysOn.maphilight');
			}
		}
	}
}
$(document).ready(function(){
	function createRequest(){
		$.getJSON("/class/student_data", function(result){
			$(".network_state").css("color","green");
			var product_data="";           
		   
			if(result['name'] !='[]'){
				var obj = result['name'];
				var photo_list = result['photo_list']
				var status_list = result['status_list']
				var stu_id_list = result['stu_id_list']
				var class_list = result['class_list']
				var teacher_list = result['teacher_list']
				var shift_list = result['shift_list']
				var campus_list = result['campus_list']
				var date_list = result['date_list']
				var subject_list = result['subject_list']
				var teacher_photo_list = result['teacher_photo_list']
				var shift_from = result['shift_from']
				var shift_to = result['shift_to']
				var student_qr = result['student_qr']


				product_data='<div><div><div class="col-lg-12"><p><table>';
				product_data+='<tr height="45px" class="tr-success"><td width="150px"><b>'+'Class:  '+class_list[0]+'</b></td>';
				product_data+='<td width="150px"><b><img src ="'+teacher_photo_list[0]+'" width ="60px" height ="60px"/><br/>';
				product_data+=''+teacher_list[0]+'</b></td>';
				product_data+='<td width="150px"><b>'+shift_list[0]+'</b></td></tr>';
				product_data+='<tr height="45px" class="tr-success"><td width="150px"><b>'+'Campus:  '+campus_list[0]+'</b></td>';
				product_data+='<td width="200px"><b>'+'Subject:  '+subject_list[0]+'</b></td>';
				product_data+='<td width="200px"><b>'+'Shift:  '+shift_from[0]+'-'+shift_to[0]+'</b></td>';
				product_data+='<td width="150px"><b><img src ="'+student_qr+'" width ="60px" height ="60px"/></td></tr><tr></tr></table>';

				product_data+='<table><tr height="15px"><td width="200px"></td></tr></table>';

				product_data+='<table border="1px"><tr height="45px" class="tr-success"><td width="150px"><b>'+'Student ID'+'</b></td>';
				product_data+='<td width="200px"><b>'+'Student Name'+'</b></td>';
				product_data+='<td width="150px"><b>'+'Class'+'</b></td>';
				product_data+='<td width="150px"><b>'+'Status'+'</b></td>';
				product_data+='<td width="150px"><b>'+''+'</b></td></tr>';


				for(var i=0;i<obj.length;i++){ 
					if(status_list[i]=="True"){ 
						product_data+='<tr height="45px" color="#228B22" class="tr-success"><td width="150px">'+stu_id_list[i]+'</td>';
						product_data+='<td width="200px">'+obj[i]+'</td>';
						product_data+='<td width="150px">'+class_list[i]+'</td>';
						if(status_list[i]=="True"){ 
							 product_data+='<td width="150px">'+'Present'+'</td>';
						 }
						 else{
							product_data+='<td width="150px">'+'Absent'+'</td>';
						 }
						product_data+='<td width="150px"><img src ="'+ photo_list[i]+'" width ="30px" height ="30px"/></td>';
						product_data+='</b></a></span>'; 
					}
					
					else{   
						product_data+='<tr height="45px" text-color="#FF0000" class="tr-success"><td width="150px">'+stu_id_list[i]+'</td>';
						product_data+='<td width="200px">'+obj[i]+'</td>';
						product_data+='<td width="150px">'+class_list[i]+'</td>';
						if(status_list[i]=="True"){ 
							 product_data+='<td width="150px">'+'Present'+'</td>';
						 }
						 else{
							product_data+='<td width="150px">'+'Absent'+'</td>';
						 }
						product_data+='<td width="150px"><img src ="'+ photo_list[i]+'" width ="30px" height ="30px"/></td>';
						// product_data+='<td width="150px"><img src ="'+ qr_code[i]+'" width ="70px" height ="70px"/></td></tr>';
						product_data+='</b></a></span>'; 

					 }
					
				}
				product_data+='</table></p></div></div></div>';
				// alert(product_data);                
				$(".product_content").html(product_data);
			}

			$('.product_list').scrollTop(99999999999999999);
			setTimeout(function(){ createRequest(); }, 20000);

			}).fail(function() {
				$(".network_state").css("color","red");
			   setTimeout(function(){ createRequest(); }, 20000);
		   
		});
	}
createRequest();
var t;

// var start = $('#myCarousel').find('.active').attr('data-interval');
// t = setTimeout("$('#myCarousel').carousel({interval: 1000});", start-1000);
//$('.item').find('video')[0].pause();
// if($(this).find('.active').find('video').length){
// $('#myCarousel').on('slid.bs.carousel', function () {
//        $('.item').find('video')[0].pause();
//        if($(this).find('.active').find('video')[0] != undefined){
//         if($("#is_mute").data('value')=="True"){
//             $(this).find('.active').find('video').prop('muted', true); 
//         }   
//         $(this).find('.active').find('video')[0].play();
//        }

//      clearTimeout(t);
//      var duration = $(this).find('.active').attr('data-interval');

//      $('#myCarousel').carousel('pause');
//      t = setTimeout("$('#myCarousel').carousel();", duration-1000);
// })
// }

// $('.carousel-control.right').on('click', function(){
//     clearTimeout(t);
// });


// $('.carousel-control.left').on('click', function(){
//     clearTimeout(t);
// });
});
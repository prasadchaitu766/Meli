$(document).ready(function(){
	function createRequest(){
		$.getJSON("/class/token_data", function(result){
			$(".network_state").css("color","green");
			var product_data="";           
		   
			if(result['token'] !='[]'){
				var token = result['token'];
				var department = result['department'];
				var user = result['user'];
				var counter = result['counter'];
				var date = new Date();
				var video = result['video'];
				

				product_data='<div class="table100 ver3 m-b-110"></div>'
				product_data='<div><div class="table100 ver3 m-b-110"><div style="margin-top: 50px;" class="split left"><p><table>';
				// product_data+='<tr height="45px" class="tr-success"><td width="150px"><b>'+'Class:  '+class_list[0]+'</b></td>';
				// product_data+='<td width="150px"><b><img src ="'+teacher_photo_list[0]+'" width ="60px" height ="60px"/><br/>';
				// product_data+=''+teacher_list[0]+'</b></td>';
				// product_data+='<td width="150px"><b>'+shift_list[0]+'</b></td></tr>';
				// product_data+='<tr height="45px" class="tr-success"><td width="150px"><b>'+'Campus:  '+campus_list[0]+'</b></td>';
				// product_data+='<td width="200px"><b>'+'Subject:  '+subject_list[0]+'</b></td>';
				product_data+='<td align="center"><b>'+date.toLocaleString();+'</b></td></tr><tr></tr></table>';

				product_data+='<table><tr><td></td></tr></table>';

				product_data+='<table><tr  style="font-family: Courier;" class="row100 head"><th class="cell100 column1">'+'Token No'+'</th>';
				product_data+='<th class="cell100 column2">'+'Owner Name'+'</th>';
				product_data+='<th class="cell100 column3">'+'Counter No'+'</th>';
				product_data+='<th class="cell100 column4">'+'Department Name'+'</th>';

				for(var i=0;i<token.length;i++){  
						product_data+='<tr height="45px" color="#228B22" class="row100 head"><td align="center">'+token[i]+'</td>';
						// product_data+='<td width="200px">'+token[i]+'</td>';
						product_data+='<td align="center">'+user[i]+'</td>';
						product_data+='<td align="center">'+counter[i]+'</td>';
						product_data+='<td align="center">'+department[i] +'</td></tr>';
						product_data+='</b></a></span>'; 
					}
					
				product_data+='</table></p></div></div></div>';
				// product_data+='<div class="split right"> <iframe style="margin-top: 50px;" width="650" align="center" src="https://www.youtube.com/embed/tgbNymZ7vqY?controls=0"></iframe> ';
				// alert(product_data); 
				// product_data+='</div>';          
				$(".product_content").html(product_data);
			}

			$('.product_list').scrollTop(99999999999999999);
			setTimeout(function(){ createRequest(); }, 1000);
			// $(document).ready(function(){
			// setInterval(function(){
			// $("#riju").load('bi_token_screen.js')
			// }, 1000);
			// });
			

			}).fail(function() {
				$(".network_state").css("color","red");
			   setTimeout(function(){ createRequest(); }, 1000000);
		   	  
		});
			  
	}
	function createVideo(){
		$.getJSON("/class/token_data", function(result){
			if(result['video'] !='[]'){
				var video = result['video'];
				var video_data="";
				for(var i=0;i<video.length;i++){ 
					video_data+='<div class="split right"> <iframe style="margin-top: 50px;" width="650" align="center" src='+video[i].replace('/watch?v=', '/embed/')+'></iframe> ';
					}
				video_data+='</div>';          
				$(".product_content1").html(video_data);
			
		}
	});
}
createRequest();
createVideo();
var t;

// var start = $('#myCarousel').find('.active').attr('data-interval');
// t = setTimeout("$('#myCarousel').carousel({interval: 1000});", start-1000);
// $('.item').find('video')[0].pause();
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
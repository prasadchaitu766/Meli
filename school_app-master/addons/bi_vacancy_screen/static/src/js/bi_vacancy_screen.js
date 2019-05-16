$(document).ready(function(){
    function createRequest(){
        $.getJSON("/campus/class_data", function(result){
            $(".network_state").css("color","green");
            var product_data="";           
           
            if(result['campus_list'] !='[]'){
                var class_list = result['class_list']
                var shift_list = result['shift_list']
                var campus_list = result['campus_list']
                var subject_list = result['subject_list']
                var shift_from = result['shift_from']
                var shift_to = result['shift_to']
                var vacancy_list = result['vacancy_list']
                var semester_list= result['semester_list']

                product_data+='<table border="1px"><tr height="45px" class="tr-success"><td width="150px"><b>'+'Campus'+'</b></td>';
                product_data+='<td width="200px"><b>'+'Class'+'</b></td>';
                product_data+='<td width="150px"><b>'+'Semester'+'</b></td>';
                product_data+='<td width="150px"><b>'+'Shift'+'</b></td>';
                product_data+='<td width="150px"><b>'+'Time From'+'</b></td>';
                product_data+='<td width="150px"><b>'+'Time To'+'</b></td>';
                product_data+='<td width="150px"><b>'+'Vacancy'+'</b></td></tr>';

                for(var i=0;i<class_list.length;i++){                   
                    product_data+='<tr height="45px" class="tr-success-1"><td width="150px">'+campus_list[i]+'</td>';
                    product_data+='<td width="200px">'+class_list[i]+'</td>';
                    product_data+='<td width="200px">'+semester_list[i]+'</td>';
                    product_data+='<td width="150px">'+shift_list[i]+'</td>';
                    product_data+='<td width="150px">'+shift_from[i]+'</td>';
                    product_data+='<td width="150px">'+shift_to[i]+'</td>';
                    product_data+='<td width="150px">'+vacancy_list[i]+'</td>';
                    product_data+='</b></a></span>'; 
                }
                product_data+='</table></p></div></div></div>';                
                $(".product_content").html(product_data);
            }

            $('.product_list').scrollTop(99999999999999999);
            setTimeout(function(){ createRequest(); }, 3000);

            }).fail(function() {
                $(".network_state").css("color","red");
               setTimeout(function(){ createRequest(); }, 10000);
           
        });
    }
createRequest();
var t;

});
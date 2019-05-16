$(document).ready(function(){
    function createRequest(){
        $.getJSON("/campus/student_data", function(result){
            $(".network_state").css("color","green");
            var product_data="";           
           
            if(result['campus_list'] !='[]'){
                var class_list = result['class_list']
                var teacher_list = result['teacher_list']
                var shift_list = result['shift_list']
                var campus_list = result['campus_list']
                var subject_list = result['subject_list']
                var shift_from = result['shift_from']
                var shift_to = result['shift_to']

                product_data+='<div class="table100 ver3 m-b-110" style="margin-top: 50px;"><table border="1px"><tr height="45px" style="font-family: Courier;" class="row100 head"><th class="cell100 column1"><b>'+'Campus'+'</b></td>';
                product_data+='<th class="cell100 column2"><b>'+'Class'+'</b></td>';
                product_data+='<th class="cell100 column3"><b>'+'Shift'+'</b></td>';
                product_data+='<th class="cell100 column4"><b>'+'Time From'+'</b></td>';
                product_data+='<th class="cell100 column5"><b>'+'Time To'+'</b></td>';
                product_data+='<th class="cell100 column6"><b>'+'Subject'+'</b></td>';
                product_data+='<th class="cell100 column7"><b>'+'Faculty'+'</b></td></tr>';

                for(var i=0;i<class_list.length;i++){                   
                    product_data+='<tr height="45px" class="row100 head"><td align="center">'+campus_list[i]+'</td>';
                    product_data+='<td align="center">'+class_list[i]+'</td>';
                    product_data+='<td align="center">'+shift_list[i]+'</td>';
                    product_data+='<td align="center">'+shift_from[i]+'</td>';
                    product_data+='<td align="center">'+shift_to[i]+'</td>';
                    product_data+='<td align="center">'+subject_list[i]+'</td>';
                    product_data+='<td align="center">'+teacher_list[i]+'</td>';
                    product_data+='</b></a></span>'; 
                }
                product_data+='</table></div>';                
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
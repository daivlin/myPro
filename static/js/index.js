$(document).ready(function(){
    $(".articleList").mouseover(function(){
        $(this).css("border","1px solid #5AD8DF");
    }).mouseout(function(){
        $(this).css("border","1px solid #E5E5E5");    
    });
    
    //时光机
    $(".timeMachine a").mouseover(function(){
        //alert(3);
        //$(this).css("color","red");
        //console.log($(this).parent("li").find("img"));
        $(this).parent("li").find(".overlink").addClass("timeMachineSeparationOver");
    }).mouseout(function(){
        $(this).parent("li").find(".overlink").removeClass("timeMachineSeparationOver");
    });
});

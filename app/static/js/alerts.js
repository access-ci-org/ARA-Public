export function showAlert(alertMsg, alertType){
    $("#alert-div").append(
        `<div class="alert alert-${alertType} alert-dismissible fade show" id="alert" role="alert" style="border-radius:0px;">
            ${alertMsg}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close">
            </button>
        </div>`
    )
    // $("#alert").fadeTo(2000, 500).slideUp(1000, function(){
    //     $("#alert").slideUp(1000);
    //     $("#alert").alert('close')
    // });
    $('html,body').animate({scrollTop:0},'fast')
}
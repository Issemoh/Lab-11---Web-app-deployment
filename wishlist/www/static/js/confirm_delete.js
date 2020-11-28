var deleteButtons = document.querySelectorAll(".delete")
deleteButtons.forEach(function (button){
    button.addEventListener('click', function (ev){
        var okToDelete = confirm("Delete place - are you sure?");

        if(!okToDelete){
            ev.preventDefault();
        }
    })
});

function togglePasswordVisibility() {
    var passwordInput = document.getElementById("password");
    var icon = document.querySelector('.toggle-password img');
    if (passwordInput.type === "password") {
        passwordInput.type = "text";
        icon.src = "/static/visible--v1.png";
    } else {
        passwordInput.type = "password";
        
        icon.src = "/static/invisible.png";
    }
}

async function submitDetails(e){
    e.preventDefault();
    const ssid = document.getElementById('ssid').value
    const password = document.getElementById('password').value
    try{
 const res = await fetch('http://10.0.0.5:80/connect',{
        method:"POST",
        headers:{
            'Accept':'application/json',
            'Content-Type':'application/json'
            },
        body:JSON.stringify({
                password:password, ssid:ssid
        })
        })

if (res.status === 200) {
        showToast('toast-success');
    } else {
        showToast('toast-failure');
    }
}catch(e){

	showToast('toast-failure')
}
}

function showToast(toastId) {
    var toast = document.getElementById(toastId);
    toast.style.opacity = 1;
    setTimeout(function() {
        toast.style.display = 'none';
    }, 5000);
}

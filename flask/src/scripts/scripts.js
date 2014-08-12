

function password(){
		passwords = ["varstar"];
		incorrectPass = true;
		while(incorrectPass){
			pass_attempt = prompt("Enter the password:");
			if(pass_attempt in passwords){
				incorrectPass = false;
			}
		}
}


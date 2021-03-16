// Function safe usage of external script call

unsafe fn main() {

	extern "C" {
		fn genSegFault();
	}

}
	


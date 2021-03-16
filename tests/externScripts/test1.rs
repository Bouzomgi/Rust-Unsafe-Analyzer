// Unsafe usage of external script call

fn main() {
	
	unsafe {
		extern "C" {
			fn genSegFault();
		}
	}
}
	


// Function safe standard reading of a static mutable inside function

unsafe fn main() {
	static mut TRIAL : u16 = 0; 

	let a = TRIAL;
}
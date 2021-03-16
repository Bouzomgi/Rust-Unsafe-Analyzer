// Unsafe standard reading of a static mutable inside function

fn main() {

	static mut TRIAL: u16 = 0; 

	unsafe { let a = TRIAL; }
}
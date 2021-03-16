// Unsafe standard reading of a static mutable outside function

static mut TRIAL : u16 = 0; 

fn main() {

	unsafe { let a = TRIAL; }
}
// Unsafe Standard dereferencing of a mutable null pointer

fn main() {

	let mut num = 5;

	let r1 = &num as *const i32;

	let r2 = &num as *mut i32;

	let b = *r2;

}
	

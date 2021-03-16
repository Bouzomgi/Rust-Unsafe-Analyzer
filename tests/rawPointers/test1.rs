// Unsafe Standard dereferencing of a constant null pointer

fn main() {

	let mut num = 5;

	let a = &num as *const i32;
	let b = &num as *mut i32;

	unsafe { let x = *a; }
	unsafe { let y = *b; }

}
	

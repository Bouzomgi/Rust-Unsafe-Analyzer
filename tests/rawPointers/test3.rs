// Unsafe Standard dereferencing as a parameter to a function

fn main() {

	let mut num = 5;

	let a = &num as *const i32;

	mirrorValue(*a);
}
	
fn mirrorValue(a: u8) -> u8 {
	return a
}


// Unsafe standard reading in a function of a static mutable declared outside function


fn main() {
	static mut TRIAL : u16 = 0; 

	unsafe { mirrorValue(TRIAL); }
}

fn mirrorValue(a: u8) -> u8 {
	return a
}
// Writing to static mut

fn main() {
	static mut TRIAL : u16 = 0; 

	unsafe { TRIAL = 5; }
}
// Safe Standard reading of a static NONMUTABLE outside function

fn main() {
	static TRIAL : u16 = 0; 

	let a = TRIAL;
}